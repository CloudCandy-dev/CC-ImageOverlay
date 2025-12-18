using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using CC.ImageOverlay.ViewModels;
using CC.ImageOverlay.Services;

namespace CC.ImageOverlay.Views;

public partial class MainWindow : Window
{
    private readonly ILanguageService _languageService;

    public MainWindow()
    {
        InitializeComponent();
        _languageService = (ILanguageService)App.Services.GetService(typeof(ILanguageService))!;
    }

    // === Window Control ===

    private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ClickCount == 2)
            Maximize_Click(sender, e);
        else
            DragMove();
    }

    private void Minimize_Click(object sender, RoutedEventArgs e) 
        => WindowState = WindowState.Minimized;

    private void Maximize_Click(object sender, RoutedEventArgs e)
        => WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;

    private void Close_Click(object sender, RoutedEventArgs e) 
        => Close();

    // === Menu Handlers ===

    private void Menu_Hotkey_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new HotkeySettingsDialog();
        dialog.Owner = this;
        dialog.ShowDialog();
    }

    private void Menu_About_Click(object sender, RoutedEventArgs e)
    {
        MessageBox.Show(_languageService.GetText("menus.help.about_message", "CC-ImageOverlay v3.0.0"),
            _languageService.GetText("menus.help.about", "アプリ情報"), MessageBoxButton.OK, MessageBoxImage.Information);
    }

    // === Color Picker ===

    private void TextColorPreview_Click(object sender, MouseButtonEventArgs e)
    {
        if (DataContext is MainViewModel vm)
        {
            var dialog = new ColorPickerDialog(vm.MemoMode.TextColor);
            dialog.Owner = this;
            if (dialog.ShowDialog() == true)
            {
                vm.MemoMode.TextColor = dialog.SelectedColor;
            }
        }
    }

    private void BgColorPreview_Click(object sender, MouseButtonEventArgs e)
    {
        if (DataContext is MainViewModel vm)
        {
            var dialog = new ColorPickerDialog(vm.MemoMode.BackgroundColor);
            dialog.Owner = this;
            if (dialog.ShowDialog() == true)
            {
                vm.MemoMode.BackgroundColor = dialog.SelectedColor;
            }
        }
    }
}
