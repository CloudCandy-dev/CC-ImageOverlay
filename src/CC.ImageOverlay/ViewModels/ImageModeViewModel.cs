using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CC.ImageOverlay.Models;
using CC.ImageOverlay.Services;
using Microsoft.Win32;

namespace CC.ImageOverlay.ViewModels;

public partial class ImageModeViewModel : ViewModelBase
{
    private readonly ILanguageService _languageService;
    private readonly IOverlayService _overlayService;

    [ObservableProperty]
    private string? _imagePath;

    [ObservableProperty]
    private int _positionX;

    [ObservableProperty]
    private int _positionY;

    [ObservableProperty]
    private double _opacity = 80;

    [ObservableProperty]
    private double _scale = 100;

    [ObservableProperty]
    private int _imageWidth = 400;

    [ObservableProperty]
    private int _imageHeight = 300;

    [ObservableProperty]
    private bool _isClickThrough = true;

    [ObservableProperty]
    private bool _hasImage;

    [ObservableProperty]
    private double _aspectRatio = 1.0;

    [ObservableProperty]
    private int _monitorWidth = 1920;

    [ObservableProperty]
    private int _monitorHeight = 1080;

    [ObservableProperty]
    private double _maxScale = 200;

    private int _originalWidth;
    private int _originalHeight;
    private bool _isUpdating;

    public ImageModeViewModel(ILanguageService languageService, IOverlayService overlayService)
    {
        _languageService = languageService;
        _overlayService = overlayService;
        _languageService.LanguageChanged += OnLanguageChanged;
    }

    // === Localized Text ===

    public string LabelImageSelection
        => _languageService.GetText("ui_controls.image_mode.image_selection.title", "画像選択");

    public string LabelOverlaySettings
        => _languageService.GetText("ui_controls.image_mode.overlay_settings.title", "オーバーレイ設定");

    public string ButtonSelectImage
        => _languageService.GetText("ui_controls.image_mode.image_selection.browse_button", "画像を選択");

    public string LabelOpacity
        => _languageService.GetText("ui_controls.image_mode.overlay_settings.opacity", "透明度");

    public string LabelScale
        => _languageService.GetText("ui_controls.image_mode.overlay_settings.scale", "スケール");

    public string LabelClickThrough
        => _languageService.GetText("ui_controls.image_mode.overlay_settings.click_through", "クリック透過");

    public string LabelImagePosition
        => "📍 " + _languageService.GetText("overlay_controls.position.title", "表示位置");

    public string LabelMonitor
        => _languageService.GetText("ui_controls.image_mode.overlay_settings.monitor", "モニター:");

    public string LabelImageScale
        => _languageService.GetText("ui_controls.image_mode.overlay_settings.scale", "スケール");

    public string SelectedImagePathText
        => string.IsNullOrEmpty(ImagePath) 
            ? _languageService.GetText("ui_controls.image_mode.image_selection.no_selection", "画像が選択されていません")
            : System.IO.Path.GetFileName(ImagePath);

    // === Commands ===

    [RelayCommand]
    private async Task SelectImage()
    {
        var dialog = new OpenFileDialog
        {
            Filter = _languageService.GetText(
                "ui_controls.common.file_dialogs.image_files_filter",
                "画像ファイル (*.png *.jpg *.jpeg *.gif *.bmp)|*.png;*.jpg;*.jpeg;*.gif;*.bmp|すべてのファイル (*.*)|*.*"),
            Title = _languageService.GetText(
                "ui_controls.common.file_dialogs.select_image_title",
                "画像ファイルを選択")
        };

        if (dialog.ShowDialog() == true)
        {
            ImagePath = dialog.FileName;
            HasImage = true;
            await LoadImageDimensionsAsync(dialog.FileName);
            
            if (_overlayService.IsVisible)
            {
                UpdateOverlay(null); // Monitor will be provided by caller or managed centrally
            }
        }
    }

    [RelayCommand]
    private void ClearImage()
    {
        ImagePath = null;
        HasImage = false;
        ImageWidth = 400;
        ImageHeight = 300;
        _originalWidth = 0;
        _originalHeight = 0;
        RecalculateMaxScale();
        if (_overlayService.IsVisible) _overlayService.Hide();
    }

    [RelayCommand]
    public void ToggleOverlay(MonitorInfo? monitor)
    {
        if (_overlayService.IsVisible)
        {
            _overlayService.Hide();
        }
        else
        {
            if (string.IsNullOrEmpty(ImagePath) || monitor == null) return;
            _overlayService.ShowImageOverlay(ImagePath, Opacity / 100.0, ImageWidth, ImageHeight, PositionX, PositionY, monitor);
        }
    }

    public void UpdateOverlay(MonitorInfo? monitor)
    {
        if (!_overlayService.IsVisible || string.IsNullOrEmpty(ImagePath) || monitor == null) return;
        _overlayService.UpdateImageOverlay(ImagePath, Opacity / 100.0, ImageWidth, ImageHeight, PositionX, PositionY, monitor);
    }

    private async Task LoadImageDimensionsAsync(string path)
    {
        if (string.IsNullOrEmpty(path)) return;

        try
        {
            await Task.Run(() =>
            {
                using var stream = new System.IO.FileStream(path, System.IO.FileMode.Open, System.IO.FileAccess.Read);
                var decoder = System.Windows.Media.Imaging.BitmapDecoder.Create(
                    stream,
                    System.Windows.Media.Imaging.BitmapCreateOptions.IgnoreColorProfile,
                    System.Windows.Media.Imaging.BitmapCacheOption.None);

                var frame = decoder.Frames[0];
                _originalWidth = frame.PixelWidth;
                _originalHeight = frame.PixelHeight;
                AspectRatio = (double)_originalWidth / _originalHeight;
            });

            // Recalculate max scale based on new image dimensions
            RecalculateMaxScale();

            // Initial scale calculation if needed
            UpdateSizeFromScale();
        }
        catch
        {
            ImageWidth = 400;
            ImageHeight = 300;
        }
    }

    private void UpdateSizeFromScale()
    {
        if (_isUpdating || _originalWidth <= 0) return;
        _isUpdating = true;
        
        // Recalculate MaxScale if needed (though it should be handled by handlers)
        RecalculateMaxScale();

        // Ensure Scale is within limits
        if (Scale > MaxScale)
        {
            Scale = MaxScale;
        }

        var newWidth = Math.Max(50, (int)(_originalWidth * (Scale / 100.0)));
        var newHeight = Math.Max(50, (int)(_originalHeight * (Scale / 100.0)));

        // Ensure position + size doesn't exceed monitor bounds
        // Adjust position if necessary to keep image within screen
        if (PositionX + newWidth > MonitorWidth)
        {
            PositionX = Math.Max(0, MonitorWidth - newWidth);
        }
        if (PositionY + newHeight > MonitorHeight)
        {
            PositionY = Math.Max(0, MonitorHeight - newHeight);
        }

        ImageWidth = newWidth;
        ImageHeight = newHeight;

        _isUpdating = false;
    }

    private void RecalculateMaxScale()
    {
        if (_originalWidth <= 0 || _originalHeight <= 0)
        {
            MaxScale = 200;
            return;
        }

        // Limit scale so image doesn't exceed monitor size
        // We also cap at 1000% to avoid extreme values for tiny images
        double scaleToFitW = ((double)MonitorWidth / _originalWidth) * 100.0;
        double scaleToFitH = ((double)MonitorHeight / _originalHeight) * 100.0;
        
        MaxScale = Math.Min(1000.0, Math.Min(scaleToFitW, scaleToFitH));
        
        // Ensure MinScale is also reasonable (don't let it go too low)
        if (MaxScale < 10) MaxScale = 10;

        // Notify UI that MaxScale changed (in case binding didn't pick it up)
        OnPropertyChanged(nameof(MaxScale));
    }

    partial void OnImageWidthChanged(int value)
    {
        if (_isUpdating || _originalWidth <= 0) return;
        _isUpdating = true;

        // Clamp width to monitor pixels
        var clampedWidth = Math.Clamp(value, 50, MonitorWidth);
        var targetScale = (clampedWidth / (double)_originalWidth) * 100.0;
        
        // Ensure height doesn't exceed monitor
        var targetHeight = (int)(_originalHeight * (targetScale / 100.0));
        if (targetHeight > MonitorHeight)
        {
            targetScale = ((double)MonitorHeight / _originalHeight) * 100.0;
        }

        Scale = Math.Clamp(targetScale, 10, MaxScale);
        var newWidth = (int)(_originalWidth * (Scale / 100.0));
        var newHeight = (int)(_originalHeight * (Scale / 100.0));

        // Adjust position if image would extend beyond screen
        if (PositionX + newWidth > MonitorWidth)
        {
            PositionX = Math.Max(0, MonitorWidth - newWidth);
        }
        if (PositionY + newHeight > MonitorHeight)
        {
            PositionY = Math.Max(0, MonitorHeight - newHeight);
        }

        ImageWidth = newWidth;
        ImageHeight = newHeight;

        _isUpdating = false;
    }

    partial void OnMonitorWidthChanged(int value)
    {
        RecalculateMaxScale();
        UpdateSizeFromScale();
    }

    partial void OnMonitorHeightChanged(int value)
    {
        RecalculateMaxScale();
        UpdateSizeFromScale();
    }

    partial void OnScaleChanged(double value)
    {
        UpdateSizeFromScale();
    }

    partial void OnImagePathChanged(string? value)
    {
        OnPropertyChanged(nameof(SelectedImagePathText));
    }

    private void OnLanguageChanged(object? sender, string lang)
    {
        OnPropertyChanged(nameof(LabelImageSelection));
        OnPropertyChanged(nameof(LabelOverlaySettings));
        OnPropertyChanged(nameof(ButtonSelectImage));
        OnPropertyChanged(nameof(LabelOpacity));
        OnPropertyChanged(nameof(LabelScale));
        OnPropertyChanged(nameof(LabelClickThrough));
        OnPropertyChanged(nameof(LabelImagePosition));
        OnPropertyChanged(nameof(LabelMonitor));
        OnPropertyChanged(nameof(SelectedImagePathText));
    }
}
