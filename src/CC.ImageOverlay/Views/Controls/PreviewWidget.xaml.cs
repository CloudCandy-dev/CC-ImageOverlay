using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.Extensions.DependencyInjection;

namespace CC.ImageOverlay.Views.Controls;

public partial class PreviewWidget : UserControl, INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    private bool _isDragging;
    private bool _isResizing;
    private Point _dragStartPoint;
    private double _overlayStartLeft;
    private double _overlayStartTop;
    private double _overlayStartWidth;
    private double _overlayStartHeight;

    // Dependency Properties
    public static readonly DependencyProperty MonitorWidthProperty =
        DependencyProperty.Register(nameof(MonitorWidth), typeof(int), typeof(PreviewWidget),
            new PropertyMetadata(1920, OnMonitorSizeChanged));

    public static readonly DependencyProperty MonitorHeightProperty =
        DependencyProperty.Register(nameof(MonitorHeight), typeof(int), typeof(PreviewWidget),
            new PropertyMetadata(1080, OnMonitorSizeChanged));

    public static readonly DependencyProperty OverlayXProperty =
        DependencyProperty.Register(nameof(OverlayX), typeof(int), typeof(PreviewWidget),
            new FrameworkPropertyMetadata(0, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault, OnOverlayPositionChanged));

    public static readonly DependencyProperty OverlayYProperty =
        DependencyProperty.Register(nameof(OverlayY), typeof(int), typeof(PreviewWidget),
            new FrameworkPropertyMetadata(0, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault, OnOverlayPositionChanged));

    public static readonly DependencyProperty OverlayWidthProperty =
        DependencyProperty.Register(nameof(OverlayWidth), typeof(int), typeof(PreviewWidget),
            new FrameworkPropertyMetadata(400, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault, OnOverlaySizeChanged));

    public static readonly DependencyProperty OverlayHeightProperty =
        DependencyProperty.Register(nameof(OverlayHeight), typeof(int), typeof(PreviewWidget),
            new FrameworkPropertyMetadata(300, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault, OnOverlaySizeChanged));

    // Aspect ratio (width / height) - 0 means no lock
    public static readonly DependencyProperty AspectRatioProperty =
        DependencyProperty.Register(nameof(AspectRatio), typeof(double), typeof(PreviewWidget),
            new PropertyMetadata(0.0));

    public int MonitorWidth
    {
        get => (int)GetValue(MonitorWidthProperty);
        set => SetValue(MonitorWidthProperty, value);
    }

    public int MonitorHeight
    {
        get => (int)GetValue(MonitorHeightProperty);
        set => SetValue(MonitorHeightProperty, value);
    }

    public int OverlayX
    {
        get => (int)GetValue(OverlayXProperty);
        set => SetValue(OverlayXProperty, value);
    }

    public int OverlayY
    {
        get => (int)GetValue(OverlayYProperty);
        set => SetValue(OverlayYProperty, value);
    }

    public int OverlayWidth
    {
        get => (int)GetValue(OverlayWidthProperty);
        set => SetValue(OverlayWidthProperty, value);
    }

    public int OverlayHeight
    {
        get => (int)GetValue(OverlayHeightProperty);
        set => SetValue(OverlayHeightProperty, value);
    }

    /// <summary>
    /// Aspect ratio (width / height). Set to 0 or less for free resize.
    /// </summary>
    public double AspectRatio
    {
        get => (double)GetValue(AspectRatioProperty);
        set => SetValue(AspectRatioProperty, value);
    }

    // Scale factors
    private double ScaleX => PreviewCanvas.ActualWidth / MonitorWidth;
    private double ScaleY => PreviewCanvas.ActualHeight / MonitorHeight;

    public PreviewWidget()
    {
        InitializeComponent();
        Loaded += OnLoaded;
        Unloaded += OnUnloaded;
        SizeChanged += OnSizeChanged;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        UpdateOverlayRect();
        
        var languageService = App.Services.GetService<Services.ILanguageService>();
        if (languageService != null)
        {
            languageService.LanguageChanged += OnLanguageChanged;
            UpdateTexts(languageService);
        }
    }

    private void OnUnloaded(object sender, RoutedEventArgs e)
    {
        var languageService = App.Services.GetService<Services.ILanguageService>();
        if (languageService != null)
        {
            languageService.LanguageChanged -= OnLanguageChanged;
        }
    }

    private void OnLanguageChanged(object? sender, string e)
    {
        if (App.Services.GetService<Services.ILanguageService>() is { } service)
        {
            UpdateTexts(service);
        }
    }

    private void UpdateTexts(Services.ILanguageService languageService)
    {
        if (LabelPositionXPrefix != null)
            LabelPositionXPrefix.Text = languageService.GetText("ui_controls.common.preview.labels.position_x", "位置: X: ");
            
        if (LabelPositionYPrefix != null)
            LabelPositionYPrefix.Text = languageService.GetText("ui_controls.common.preview.labels.position_y", "  Y: ");
            
        if (LabelSizePrefix != null)
            LabelSizePrefix.Text = languageService.GetText("ui_controls.common.preview.labels.size", "  |  サイズ: ");
    }

    private void OnSizeChanged(object sender, SizeChangedEventArgs e)
    {
        UpdateOverlayRect();
    }

    private static void OnMonitorSizeChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is PreviewWidget widget)
            widget.UpdateOverlayRect();
    }

    private static void OnOverlayPositionChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is PreviewWidget widget)
        {
            widget.UpdateOverlayRect();
            widget.PropertyChanged?.Invoke(widget, new PropertyChangedEventArgs(e.Property.Name));
        }
    }

    private static void OnOverlaySizeChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is PreviewWidget widget)
        {
            widget.UpdateOverlayRect();
            widget.PropertyChanged?.Invoke(widget, new PropertyChangedEventArgs(e.Property.Name));
        }
    }

    private void UpdateOverlayRect()
    {
        if (PreviewCanvas.ActualWidth <= 0 || PreviewCanvas.ActualHeight <= 0)
            return;

        // Scale overlay size and position
        var scaledWidth = OverlayWidth * ScaleX;
        var scaledHeight = OverlayHeight * ScaleY;
        var scaledX = OverlayX * ScaleX;
        var scaledY = OverlayY * ScaleY;

        OverlayRect.Width = Math.Max(10, scaledWidth);
        OverlayRect.Height = Math.Max(10, scaledHeight);
        Canvas.SetLeft(OverlayRect, scaledX);
        Canvas.SetTop(OverlayRect, scaledY);

        // Position resize handle at bottom-right corner
        Canvas.SetLeft(ResizeHandle, scaledX + scaledWidth - 6);
        Canvas.SetTop(ResizeHandle, scaledY + scaledHeight - 6);

        // Update text
        PositionXText.Text = OverlayX.ToString();
        PositionYText.Text = OverlayY.ToString();
        SizeText.Text = $"{OverlayWidth}×{OverlayHeight}";
    }

    // === Drag for Position ===

    private void PreviewCanvas_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (OverlayRect.IsMouseOver && !ResizeHandle.IsMouseOver)
        {
            _isDragging = true;
            _dragStartPoint = e.GetPosition(PreviewCanvas);
            _overlayStartLeft = Canvas.GetLeft(OverlayRect);
            _overlayStartTop = Canvas.GetTop(OverlayRect);
            OverlayRect.CaptureMouse();
        }
    }

    private void PreviewCanvas_MouseMove(object sender, MouseEventArgs e)
    {
        if (!_isDragging) return;

        var currentPos = e.GetPosition(PreviewCanvas);
        var deltaX = currentPos.X - _dragStartPoint.X;
        var deltaY = currentPos.Y - _dragStartPoint.Y;

        var newLeft = _overlayStartLeft + deltaX;
        var newTop = _overlayStartTop + deltaY;

        // Use calculated scaled dimensions for consistent bounds
        var scaledWidth = OverlayWidth * ScaleX;
        var scaledHeight = OverlayHeight * ScaleY;

        // Clamp to canvas bounds
        newLeft = Math.Clamp(newLeft, 0, PreviewCanvas.ActualWidth - scaledWidth);
        newTop = Math.Clamp(newTop, 0, PreviewCanvas.ActualHeight - scaledHeight);

        Canvas.SetLeft(OverlayRect, newLeft);
        Canvas.SetTop(OverlayRect, newTop);

        // Convert back to real coordinates
        OverlayX = (int)(newLeft / ScaleX);
        OverlayY = (int)(newTop / ScaleY);

        PositionXText.Text = OverlayX.ToString();
        PositionYText.Text = OverlayY.ToString();
    }

    private void PreviewCanvas_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (_isDragging)
        {
            _isDragging = false;
            OverlayRect.ReleaseMouseCapture();
        }
    }

    // === Resize Handle for Scale ===

    private void ResizeHandle_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        _isResizing = true;
        _dragStartPoint = e.GetPosition(PreviewCanvas);
        _overlayStartWidth = OverlayRect.ActualWidth;
        _overlayStartHeight = OverlayRect.ActualHeight;
        ResizeHandle.CaptureMouse();
        e.Handled = true;
    }

    private void ResizeHandle_MouseMove(object sender, MouseEventArgs e)
    {
        if (!_isResizing) return;

        var currentPos = e.GetPosition(PreviewCanvas);
        var deltaX = currentPos.X - _dragStartPoint.X;
        var deltaY = currentPos.Y - _dragStartPoint.Y;

        int newWidth, newHeight;

        if (AspectRatio > 0)
        {
            // Maintain aspect ratio - use diagonal distance for uniform scaling
            var scaledWidth = Math.Max(20, _overlayStartWidth + deltaX);
            
            // Convert to real width and calculate height from aspect ratio
            newWidth = (int)(scaledWidth / ScaleX);
            newHeight = (int)(newWidth / AspectRatio);
        }
        else
        {
            // Free resize
            var newScaledWidth = Math.Max(20, _overlayStartWidth + deltaX);
            var newScaledHeight = Math.Max(20, _overlayStartHeight + deltaY);
            newWidth = (int)(newScaledWidth / ScaleX);
            newHeight = (int)(newScaledHeight / ScaleY);
        }

        // Clamp to reasonable values
        newWidth = Math.Clamp(newWidth, 50, MonitorWidth);
        newHeight = Math.Clamp(newHeight, 50, MonitorHeight);

        // If aspect ratio is locked, strictly enforce it within bounds
        if (AspectRatio > 0)
        {
            // First calculate height from restricted width
            newHeight = (int)(newWidth / AspectRatio);
            
            // If height exceeds monitor, clamp height and recalculate width
            if (newHeight > MonitorHeight)
            {
                newHeight = MonitorHeight;
                newWidth = (int)(newHeight * AspectRatio);
            }
        }

        OverlayWidth = newWidth;
        OverlayHeight = newHeight;

        UpdateOverlayRect();
        e.Handled = true;
    }

    private void ResizeHandle_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (_isResizing)
        {
            _isResizing = false;
            ResizeHandle.ReleaseMouseCapture();
            e.Handled = true;
        }
    }
}
