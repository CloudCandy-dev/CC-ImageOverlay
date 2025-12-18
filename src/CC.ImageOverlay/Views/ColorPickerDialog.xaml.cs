using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace CC.ImageOverlay.Views;

public partial class ColorPickerDialog : Window
{
    public Color SelectedColor { get; private set; }
    
    private double _hue = 0;
    private double _saturation = 1;
    private double _brightness = 1;
    private byte _alpha = 255;
    private bool _isLoaded = false;

    public ColorPickerDialog(Color initialColor)
    {
        InitializeComponent();
        SelectedColor = initialColor;
        _alpha = initialColor.A;
        
        Loaded += (s, e) =>
        {
            _isLoaded = true;
            AlphaSlider.Value = _alpha;
            ColorToHsb(initialColor, out _hue, out _saturation, out _brightness);
            UpdateFromHsb();
        };
    }

    private void ColorCanvas_MouseDown(object sender, MouseButtonEventArgs e)
    {
        if (!_isLoaded) return;
        ((UIElement)sender).CaptureMouse();
        UpdateColorFromCanvas(e);
    }

    private void ColorCanvas_MouseMove(object sender, MouseEventArgs e)
    {
        if (!_isLoaded) return;
        if (e.LeftButton == MouseButtonState.Pressed)
        {
            UpdateColorFromCanvas(e);
        }
        else
        {
            ((UIElement)sender).ReleaseMouseCapture();
        }
    }

    private void UpdateColorFromCanvas(MouseEventArgs e)
    {
        if (ColorCanvas.ActualWidth <= 0 || ColorCanvas.ActualHeight <= 0) return;
        
        var pos = e.GetPosition(ColorCanvas);
        var width = ColorCanvas.ActualWidth;
        var height = ColorCanvas.ActualHeight;

        _saturation = Math.Clamp(pos.X / width, 0, 1);
        _brightness = Math.Clamp(1 - pos.Y / height, 0, 1);

        UpdateFromHsb();
    }

    private void HueSlider_MouseDown(object sender, MouseButtonEventArgs e)
    {
        if (!_isLoaded) return;
        ((UIElement)sender).CaptureMouse();
        UpdateHueFromSlider(e);
    }

    private void HueSlider_MouseMove(object sender, MouseEventArgs e)
    {
        if (!_isLoaded) return;
        if (e.LeftButton == MouseButtonState.Pressed)
        {
            UpdateHueFromSlider(e);
        }
        else
        {
            ((UIElement)sender).ReleaseMouseCapture();
        }
    }

    private void UpdateHueFromSlider(MouseEventArgs e)
    {
        if (HueSlider.ActualHeight <= 0) return;
        
        var pos = e.GetPosition(HueSlider);
        var height = HueSlider.ActualHeight;
        
        _hue = Math.Clamp(pos.Y / height * 360, 0, 360);
        
        UpdateFromHsb();
    }

    private void AlphaSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (!_isLoaded) return;
        _alpha = (byte)AlphaSlider.Value;
        if (AlphaText != null) AlphaText.Text = _alpha.ToString();
        UpdatePreview();
    }

    private void UpdateFromHsb()
    {
        if (!_isLoaded) return;
        
        // Update Hue Color
        var hueColor = HsbToColor(_hue, 1, 1);
        if (HueColor != null) HueColor.Color = hueColor;

        // Update selectors
        if (ColorCanvas?.ActualWidth > 0 && ColorSelector != null)
        {
            Canvas.SetLeft(ColorSelector, _saturation * ColorCanvas.ActualWidth - 7);
            Canvas.SetTop(ColorSelector, (1 - _brightness) * ColorCanvas.ActualHeight - 7);
        }
        
        if (HueSlider?.ActualHeight > 0 && HueSelector != null)
        {
            Canvas.SetTop(HueSelector, _hue / 360 * HueSlider.ActualHeight - 2);
        }

        UpdatePreview();
    }

    private void UpdatePreview()
    {
        if (!_isLoaded) return;
        
        var color = HsbToColor(_hue, _saturation, _brightness);
        color.A = _alpha;
        SelectedColor = color;
        if (PreviewBrush != null) PreviewBrush.Color = color;
    }

    private static Color HsbToColor(double h, double s, double b)
    {
        int hi = (int)(h / 60) % 6;
        double f = h / 60 - Math.Floor(h / 60);
        
        byte v = (byte)(b * 255);
        byte p = (byte)(b * (1 - s) * 255);
        byte q = (byte)(b * (1 - f * s) * 255);
        byte t = (byte)(b * (1 - (1 - f) * s) * 255);

        return hi switch
        {
            0 => Color.FromRgb(v, t, p),
            1 => Color.FromRgb(q, v, p),
            2 => Color.FromRgb(p, v, t),
            3 => Color.FromRgb(p, q, v),
            4 => Color.FromRgb(t, p, v),
            _ => Color.FromRgb(v, p, q),
        };
    }

    private static void ColorToHsb(Color color, out double h, out double s, out double b)
    {
        double r = color.R / 255.0;
        double g = color.G / 255.0;
        double bl = color.B / 255.0;

        double max = Math.Max(r, Math.Max(g, bl));
        double min = Math.Min(r, Math.Min(g, bl));
        double delta = max - min;

        b = max;
        s = max == 0 ? 0 : delta / max;

        if (delta == 0)
        {
            h = 0;
        }
        else if (max == r)
        {
            h = 60 * (((g - bl) / delta) % 6);
        }
        else if (max == g)
        {
            h = 60 * ((bl - r) / delta + 2);
        }
        else
        {
            h = 60 * ((r - g) / delta + 4);
        }

        if (h < 0) h += 360;
    }

    private void OK_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = true;
        Close();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
