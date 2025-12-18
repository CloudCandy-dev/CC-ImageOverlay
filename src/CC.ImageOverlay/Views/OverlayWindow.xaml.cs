using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using CC.ImageOverlay.Infrastructure;

namespace CC.ImageOverlay.Views;

public partial class OverlayWindow : Window
{
    private bool _isClickThrough = true;

    public OverlayWindow()
    {
        InitializeComponent();
        Loaded += OnLoaded;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        SetClickThrough(_isClickThrough);
    }

    /// <summary>
    /// クリック透過を設定
    /// </summary>
    public void SetClickThrough(bool enable)
    {
        _isClickThrough = enable;
        var hwnd = new WindowInteropHelper(this).Handle;
        if (hwnd == IntPtr.Zero) return;

        var extendedStyle = NativeMethods.GetWindowLong(hwnd, NativeMethods.GWL_EXSTYLE);

        if (enable)
        {
            NativeMethods.SetWindowLong(hwnd, NativeMethods.GWL_EXSTYLE,
                extendedStyle | NativeMethods.WS_EX_TRANSPARENT | NativeMethods.WS_EX_LAYERED);
        }
        else
        {
            NativeMethods.SetWindowLong(hwnd, NativeMethods.GWL_EXSTYLE,
                extendedStyle & ~NativeMethods.WS_EX_TRANSPARENT);
        }
    }

    /// <summary>
    /// 画像を設定
    /// </summary>
    public void SetImage(string imagePath, double opacity, double scale)
    {
        try
        {
            var bitmap = new BitmapImage();
            bitmap.BeginInit();
            bitmap.UriSource = new Uri(imagePath, UriKind.Absolute);
            bitmap.CacheOption = BitmapCacheOption.OnLoad;
            bitmap.EndInit();
            bitmap.Freeze();

            OverlayImage.Source = bitmap;
            OverlayImage.Opacity = opacity;
            OverlayImage.Width = bitmap.PixelWidth * scale;
            OverlayImage.Height = bitmap.PixelHeight * scale;
            OverlayImage.Visibility = Visibility.Visible;
            MemoContainer.Visibility = Visibility.Collapsed;

            Width = OverlayImage.Width;
            Height = OverlayImage.Height;
        }
        catch
        {
            // Handle invalid image path
        }
    }

    /// <summary>
    /// 画像をサイズ指定で設定
    /// </summary>
    public void SetImageWithSize(string imagePath, double opacity, int width, int height)
    {
        try
        {
            var bitmap = new BitmapImage();
            bitmap.BeginInit();
            bitmap.UriSource = new Uri(imagePath, UriKind.Absolute);
            bitmap.CacheOption = BitmapCacheOption.OnLoad;
            bitmap.EndInit();
            bitmap.Freeze();

            OverlayImage.Source = bitmap;
            OverlayImage.Opacity = opacity;
            OverlayImage.Width = width;
            OverlayImage.Height = height;
            OverlayImage.Visibility = Visibility.Visible;
            MemoContainer.Visibility = Visibility.Collapsed;

            Width = width;
            Height = height;
        }
        catch
        {
            // Handle invalid image path
        }
    }

    /// <summary>
    /// メモテキストを設定
    /// </summary>
    public void SetMemo(string text, string fontFamily, double fontSize, 
        Color textColor, double textOpacity, Color backgroundColor, double bgOpacity,
        int width = 0, int height = 0)
    {
        MemoText.Text = text;
        MemoText.FontFamily = new FontFamily(fontFamily);
        MemoText.FontSize = fontSize;
        MemoText.Foreground = new SolidColorBrush(textColor) { Opacity = textOpacity };
        MemoContainer.Background = new SolidColorBrush(backgroundColor) { Opacity = bgOpacity };

        OverlayImage.Visibility = Visibility.Collapsed;
        MemoContainer.Visibility = Visibility.Visible;

        // Set window size if specified
        if (width > 0 && height > 0)
        {
            Width = width;
            Height = height;
            MemoContainer.Width = width;
            MemoContainer.Height = height;
        }
        else
        {
            // Auto-size
            SizeToContent = SizeToContent.WidthAndHeight;
        }
    }

    /// <summary>
    /// 位置を設定
    /// </summary>
    public void SetPosition(int x, int y)
    {
        Left = x;
        Top = y;
    }

    /// <summary>
    /// モニター上に配置
    /// </summary>
    public void SetMonitorPosition(int monitorLeft, int monitorTop, int overlayX, int overlayY)
    {
        Left = monitorLeft + overlayX;
        Top = monitorTop + overlayY;
    }
}
