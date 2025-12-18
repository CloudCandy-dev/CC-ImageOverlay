using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CC.ImageOverlay.Services;
using CC.ImageOverlay.Models;
using System.Windows.Media;

namespace CC.ImageOverlay.ViewModels;

public partial class MemoModeViewModel : ViewModelBase
{
    private readonly ILanguageService _languageService;
    private readonly IOverlayService _overlayService;

    [ObservableProperty]
    private string _memoText = "";

    [ObservableProperty]
    private string _fontFamily = "Noto Sans JP";

    [ObservableProperty]
    private double _fontSize = 16;

    [ObservableProperty]
    private Color _textColor = Colors.White;

    [ObservableProperty]
    private double _textOpacity = 100;

    [ObservableProperty]
    private Color _backgroundColor = Color.FromArgb(204, 0, 0, 0);

    [ObservableProperty]
    private double _backgroundOpacity = 80;

    [ObservableProperty]
    private int _positionX = 100;

    [ObservableProperty]
    private int _positionY = 100;

    [ObservableProperty]
    private int _width = 300;

    [ObservableProperty]
    private int _height = 150;

    [ObservableProperty]
    private int _monitorWidth = 1920;

    [ObservableProperty]
    private int _monitorHeight = 1080;

    public MemoModeViewModel(ILanguageService languageService, IOverlayService overlayService)
    {
        _languageService = languageService;
        _overlayService = overlayService;
        _languageService.LanguageChanged += OnLanguageChanged;
    }

    // === Font Families ===
    public static IReadOnlyList<string> AvailableFonts { get; } = new[]
    {
        "Noto Sans JP",
        "Yu Gothic UI",
        "Meiryo UI",
        "MS Gothic",
        "Segoe UI",
        "Arial"
    };

    // === Localized Text ===

    public string LabelMemoText => "📝 " + _languageService.GetText("ui_controls.memo_mode.memo_text.title", "メモテキスト");
    public string LabelMemoPosition => "📍 " + _languageService.GetText("overlay_controls.position.title", "表示位置");
    public string LabelMemoMonitor => _languageService.GetText("ui_controls.memo_mode.memo_settings.monitor", "モニター:");
    public string LabelMemoStyle => "🎨 " + _languageService.GetText("ui_controls.memo_mode.memo_settings.title", "スタイル設定");
    public string LabelMemoFont => _languageService.GetText("ui_controls.memo_mode.memo_settings.font", "フォント:");
    public string LabelMemoFontSize => _languageService.GetText("ui_controls.memo_mode.memo_settings.font_size", "サイズ:");
    public string LabelMemoWidth => _languageService.GetText("ui_controls.memo_mode.memo_settings.width", "幅:");
    public string LabelMemoHeight => _languageService.GetText("ui_controls.memo_mode.memo_settings.height", "高さ:");
    public string LabelMemoColor => _languageService.GetText("ui_controls.memo_mode.memo_settings.text_color", "文字色:");
    public string LabelMemoBgColor => _languageService.GetText("ui_controls.memo_mode.memo_settings.background_color", "背景色:");
    public string LabelMemoTextOpacity => _languageService.GetText("ui_controls.memo_mode.memo_settings.opacity", "透明度:");
    public string LabelMemoBgOpacity => _languageService.GetText("ui_controls.memo_mode.memo_settings.opacity", "背景透明度:");

    // === Commands ===

    [RelayCommand]
    private void ClearMemo()
    {
        MemoText = "";
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
            if (string.IsNullOrWhiteSpace(MemoText) || monitor == null) return;
            _overlayService.ShowMemoOverlay(MemoText, FontFamily, FontSize, TextColor, TextOpacity / 100.0, BackgroundColor, BackgroundOpacity / 100.0, Width, Height, PositionX, PositionY, monitor);
        }
    }

    public void UpdateOverlay(MonitorInfo? monitor)
    {
        if (!_overlayService.IsVisible || monitor == null) return;
        _overlayService.UpdateMemoOverlay(MemoText, FontFamily, FontSize, TextColor, TextOpacity / 100.0, BackgroundColor, BackgroundOpacity / 100.0, Width, Height, PositionX, PositionY, monitor);
    }

    // === Property Change Handlers ===

    partial void OnMemoTextChanged(string value) => UpdateOverlayIfVisible();
    partial void OnFontFamilyChanged(string value) => UpdateOverlayIfVisible();
    partial void OnFontSizeChanged(double value) => UpdateOverlayIfVisible();
    partial void OnTextColorChanged(Color value) => UpdateOverlayIfVisible();
    partial void OnBackgroundColorChanged(Color value) => UpdateOverlayIfVisible();
    partial void OnWidthChanged(int value)
    {
        // Adjust position if memo would extend beyond screen
        if (PositionX + value > MonitorWidth)
        {
            PositionX = Math.Max(0, MonitorWidth - value);
        }
        UpdateOverlayIfVisible();
    }

    partial void OnHeightChanged(int value)
    {
        // Adjust position if memo would extend beyond screen
        if (PositionY + value > MonitorHeight)
        {
            PositionY = Math.Max(0, MonitorHeight - value);
        }
        UpdateOverlayIfVisible();
    }

    private void UpdateOverlayIfVisible()
    {
        // Note: Monitor needs to be provided. This might be better handled by a central manager or by passing the monitor to the ViewModel.
        // For now, we'll assume the caller (MainViewModel) will trigger updates when monitor changes.
    }

    private void OnLanguageChanged(object? sender, string lang)
    {
        OnPropertyChanged(nameof(LabelMemoText));
        OnPropertyChanged(nameof(LabelMemoPosition));
        OnPropertyChanged(nameof(LabelMemoMonitor));
        OnPropertyChanged(nameof(LabelMemoStyle));
        OnPropertyChanged(nameof(LabelMemoFont));
        OnPropertyChanged(nameof(LabelMemoFontSize));
        OnPropertyChanged(nameof(LabelMemoWidth));
        OnPropertyChanged(nameof(LabelMemoHeight));
        OnPropertyChanged(nameof(LabelMemoColor));
        OnPropertyChanged(nameof(LabelMemoBgColor));
        OnPropertyChanged(nameof(LabelMemoTextOpacity));
        OnPropertyChanged(nameof(LabelMemoBgOpacity));
    }
}
