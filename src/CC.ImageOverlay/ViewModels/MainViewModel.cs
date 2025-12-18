using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CC.ImageOverlay.Models;
using CC.ImageOverlay.Services;
using System.Windows;
using System.ComponentModel;

namespace CC.ImageOverlay.ViewModels;

public partial class MainViewModel : ViewModelBase
{
    private readonly ILanguageService _languageService;
    private readonly IMonitorService _monitorService;
    private readonly ISettingsService _settingsService;
    private readonly IOverlayService _overlayService;

    [ObservableProperty]
    private int _selectedTabIndex;

    public ImageModeViewModel ImageMode { get; }
    public MemoModeViewModel MemoMode { get; }

    [ObservableProperty]
    private IReadOnlyList<MonitorInfo> _monitors = Array.Empty<MonitorInfo>();

    [ObservableProperty]
    private MonitorInfo? _selectedMonitor;

    [ObservableProperty]
    private bool _isOverlayVisible;

    public MainViewModel(
        ILanguageService languageService,
        IMonitorService monitorService,
        ISettingsService settingsService,
        IOverlayService overlayService,
        ImageModeViewModel imageMode,
        MemoModeViewModel memoMode)
    {
        _languageService = languageService;
        _monitorService = monitorService;
        _settingsService = settingsService;
        _overlayService = overlayService;
        ImageMode = imageMode;
        MemoMode = memoMode;

        _languageService.LanguageChanged += OnLanguageChanged;
        ImageMode.PropertyChanged += OnImageModePropertyChanged;
        MemoMode.PropertyChanged += OnMemoModePropertyChanged;

        LoadMonitors();
    }

    // === Localized Text Properties ===

    public string Title => "CC-ImageOverlay";
    public string TabImageMode => _languageService.GetText("main_window.tabs.image_mode", "画像モード");
    public string TabMemoMode => _languageService.GetText("main_window.tabs.memo_mode", "メモモード");
    public string MenuFile => _languageService.GetText("menus.file.label", "ファイル(_F)");
    public string MenuExit => _languageService.GetText("menus.file.exit", "終了(_X)");
    public string MenuSettings => _languageService.GetText("menus.settings.label", "設定(_S)");
    public string MenuLanguage => _languageService.GetText("menus.settings.language", "言語設定(_L)");
    public string MenuTheme => _languageService.GetText("menus.settings.theme", "テーマ(_T)");
    public string MenuThemeSystem => _languageService.GetText("settings.appearance.theme.system", "システムに従う");
    public string MenuThemeDark => _languageService.GetText("settings.appearance.theme.dark", "ダーク");
    public string MenuThemeLight => _languageService.GetText("settings.appearance.theme.light", "ライト");
    public string MenuHotkey => _languageService.GetText("menus.tools.hotkey_settings", "ホットキー設定(_H)");
    public string MenuHelp => _languageService.GetText("menus.help.label", "ヘルプ(_H)");
    public string MenuAbout => _languageService.GetText("menus.help.about", "アプリ情報(_A)");

    public string ActionButtonText
    {
        get
        {
            if (SelectedTabIndex == 0) // Image Mode
            {
                return IsOverlayVisible
                    ? "🎯 " + _languageService.GetText("ui_controls.action_button.hide_overlay", "オーバーレイ非表示")
                    : "🎯 " + _languageService.GetText("ui_controls.action_button.show_overlay", "オーバーレイ表示");
            }
            else // Memo Mode
            {
                return IsOverlayVisible
                    ? "📝 " + _languageService.GetText("ui_controls.action_button.hide_memo", "メモ非表示")
                    : "📝 " + _languageService.GetText("ui_controls.action_button.show_memo", "メモ表示");
            }
        }
    }

    // === Commands ===

    [RelayCommand]
    private void LoadMonitors()
    {
        Monitors = _monitorService.GetMonitors().ToList();
        SelectedMonitor = Monitors.FirstOrDefault(m => m.IsPrimary) ?? Monitors.FirstOrDefault();
    }

    [RelayCommand]
    private void ChangeLanguage(string langCode)
    {
        _settingsService.UpdateLanguage(langCode);
        _languageService.LoadLanguage(langCode);
    }

    [RelayCommand]
    private void ChangeTheme(string theme)
    {
        _settingsService.UpdateTheme(theme);
        App.SwitchTheme(theme);
    }

    [RelayCommand]
    private void ExitApp()
    {
        _overlayService.Close();
        Application.Current.Shutdown();
    }

    [RelayCommand]
    private void ToggleAction()
    {
        if (SelectedTabIndex == 0)
        {
            ImageMode.ToggleOverlay(SelectedMonitor);
            IsOverlayVisible = ImageMode.HasImage && _overlayService.IsVisible;
        }
        else
        {
            MemoMode.ToggleOverlay(SelectedMonitor);
            IsOverlayVisible = !string.IsNullOrWhiteSpace(MemoMode.MemoText) && _overlayService.IsVisible;
        }
    }

    // === Event Handlers ===

    partial void OnSelectedMonitorChanged(MonitorInfo? value)
    {
        if (value != null)
        {
            ImageMode.MonitorWidth = value.Width;
            ImageMode.MonitorHeight = value.Height;
            MemoMode.MonitorWidth = value.Width;
            MemoMode.MonitorHeight = value.Height;
        }

        if (IsOverlayVisible)
        {
            if (SelectedTabIndex == 0) ImageMode.UpdateOverlay(value);
            else MemoMode.UpdateOverlay(value);
        }
    }

    private void OnLanguageChanged(object? sender, string lang)
    {
        OnPropertyChanged(nameof(TabImageMode));
        OnPropertyChanged(nameof(TabMemoMode));
        OnPropertyChanged(nameof(MenuFile));
        OnPropertyChanged(nameof(MenuExit));
        OnPropertyChanged(nameof(MenuSettings));
        OnPropertyChanged(nameof(MenuLanguage));
        OnPropertyChanged(nameof(MenuTheme));
        OnPropertyChanged(nameof(MenuThemeSystem));
        OnPropertyChanged(nameof(MenuThemeDark));
        OnPropertyChanged(nameof(MenuThemeLight));
        OnPropertyChanged(nameof(MenuHotkey));
        OnPropertyChanged(nameof(MenuHelp));
        OnPropertyChanged(nameof(MenuAbout));
        OnPropertyChanged(nameof(ActionButtonText));
    }

    partial void OnSelectedTabIndexChanged(int value)
    {
        if (IsOverlayVisible)
        {
            _overlayService.Hide();
            IsOverlayVisible = false;
        }
        OnPropertyChanged(nameof(ActionButtonText));
    }

    partial void OnIsOverlayVisibleChanged(bool value)
    {
        OnPropertyChanged(nameof(ActionButtonText));
    }

    private void OnImageModePropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (IsOverlayVisible && SelectedTabIndex == 0)
        {
            var props = new[] { 
                nameof(ImageModeViewModel.PositionX), 
                nameof(ImageModeViewModel.PositionY), 
                nameof(ImageModeViewModel.ImageWidth), 
                nameof(ImageModeViewModel.ImageHeight), 
                nameof(ImageModeViewModel.Opacity),
                nameof(ImageModeViewModel.ImagePath)
            };
            if (props.Contains(e.PropertyName))
            {
                ImageMode.UpdateOverlay(SelectedMonitor);
            }
        }
    }

    private void OnMemoModePropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (IsOverlayVisible && SelectedTabIndex == 1)
        {
            var props = new[] { 
                nameof(MemoModeViewModel.PositionX), 
                nameof(MemoModeViewModel.PositionY), 
                nameof(MemoModeViewModel.Width), 
                nameof(MemoModeViewModel.Height), 
                nameof(MemoModeViewModel.FontSize),
                nameof(MemoModeViewModel.FontFamily),
                nameof(MemoModeViewModel.TextColor),
                nameof(MemoModeViewModel.BackgroundColor),
                nameof(MemoModeViewModel.TextOpacity),
                nameof(MemoModeViewModel.BackgroundOpacity),
                nameof(MemoModeViewModel.MemoText)
            };
            if (props.Contains(e.PropertyName))
            {
                MemoMode.UpdateOverlay(SelectedMonitor);
            }
        }
    }
}
