using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Win32;
using CC.ImageOverlay.Services;
using CC.ImageOverlay.ViewModels;
using CC.ImageOverlay.Views;

namespace CC.ImageOverlay;

public partial class App : Application
{
    private readonly ServiceProvider _serviceProvider;
    public static IServiceProvider Services { get; private set; } = null!;
    public static string CurrentTheme { get; set; } = "Dark";

    public App()
    {
        var services = new ServiceCollection();
        ConfigureServices(services);
        _serviceProvider = services.BuildServiceProvider();
        Services = _serviceProvider;
    }

    private void ConfigureServices(IServiceCollection services)
    {
        // Services
        services.AddSingleton<ILanguageService, LanguageService>();
        services.AddSingleton<IMonitorService, MonitorService>();
        services.AddSingleton<ISettingsService, SettingsService>();
        services.AddSingleton<IOverlayService, OverlayService>();
        services.AddSingleton<HotkeyService>();

        // ViewModels
        services.AddTransient<MainViewModel>();
        services.AddTransient<ImageModeViewModel>();
        services.AddTransient<MemoModeViewModel>();

        // Views
        services.AddTransient<MainWindow>();
    }

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // Shutdown when main window closes
        ShutdownMode = ShutdownMode.OnMainWindowClose;

        // Load settings
        var settingsService = _serviceProvider.GetRequiredService<ISettingsService>();
        settingsService.Load();

        // Apply theme from settings
        ApplyTheme(settingsService.CurrentSettings.Theme);

        // Load language based on settings
        var languageService = _serviceProvider.GetRequiredService<ILanguageService>();
        languageService.LoadLanguage(settingsService.CurrentSettings.Language);

        // Create and show main window
        var mainWindow = _serviceProvider.GetRequiredService<MainWindow>();
        mainWindow.DataContext = _serviceProvider.GetRequiredService<MainViewModel>();
        MainWindow = mainWindow;
        mainWindow.Show();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _serviceProvider.Dispose();
        base.OnExit(e);
    }

    /// <summary>
    /// 起動時にテーマを適用
    /// </summary>
    private void ApplyTheme(string theme)
    {
        try
        {
            CurrentTheme = theme;
            
            // System theme detection
            if (theme == "System")
            {
                theme = GetSystemTheme();
            }
            
            var mergedDicts = Resources.MergedDictionaries;
            mergedDicts.Clear();
            
            var themeFile = theme == "Light" 
                ? "Themes/RamuneSodaLightTheme.xaml" 
                : "Themes/RamuneSodaTheme.xaml";
                
            mergedDicts.Add(new ResourceDictionary 
            { 
                Source = new Uri(themeFile, UriKind.Relative) 
            });
        }
        catch (Exception ex)
        {
            // Fallback to dark theme
            CurrentTheme = "Dark";
            System.Diagnostics.Debug.WriteLine($"Theme loading failed: {ex.Message}");
        }
    }

    /// <summary>
    /// 実行時にテーマを切り替え
    /// </summary>
    public static void SwitchTheme(string theme)
    {
        try
        {
            CurrentTheme = theme;
            
            // System theme detection
            if (theme == "System")
            {
                theme = GetSystemTheme();
            }
            
            var mergedDicts = Current.Resources.MergedDictionaries;
            mergedDicts.Clear();
            
            var themeFile = theme == "Light" 
                ? "Themes/RamuneSodaLightTheme.xaml" 
                : "Themes/RamuneSodaTheme.xaml";
                
            mergedDicts.Add(new ResourceDictionary 
            { 
                Source = new Uri(themeFile, UriKind.Relative) 
            });
        }
        catch (Exception ex)
        {
            MessageBox.Show($"テーマの切り替えに失敗しました。\n{ex.Message}",
                "エラー", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    /// <summary>
    /// Windowsのシステムテーマを取得
    /// </summary>
    private static string GetSystemTheme()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(
                @"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize");
            
            if (key != null)
            {
                var value = key.GetValue("AppsUseLightTheme");
                if (value is int lightTheme)
                {
                    return lightTheme == 1 ? "Light" : "Dark";
                }
            }
        }
        catch
        {
            // Ignore registry access errors
        }
        
        return "Dark"; // Default to dark if detection fails
    }
}
