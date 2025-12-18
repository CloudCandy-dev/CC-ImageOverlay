using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace CC.ImageOverlay.Views;

public partial class HotkeySettingsDialog : Window
{
    private TextBox? _activeHotkeyBox;
    private string _overlayHotkey = "Ctrl+Shift+O";
    private string _memoHotkey = "Ctrl+Shift+M";

    public HotkeySettingsDialog()
    {
        InitializeComponent();
    }

    private void ChangeOverlayHotkey_Click(object sender, RoutedEventArgs e)
    {
        _activeHotkeyBox = OverlayHotkey;
        OverlayHotkey.Text = "キーを押してください...";
        OverlayHotkey.Focus();
    }

    private void ChangeMemoHotkey_Click(object sender, RoutedEventArgs e)
    {
        _activeHotkeyBox = MemoHotkey;
        MemoHotkey.Text = "キーを押してください...";
        MemoHotkey.Focus();
    }

    private void Hotkey_PreviewKeyDown(object sender, KeyEventArgs e)
    {
        if (_activeHotkeyBox == null || _activeHotkeyBox != sender) return;

        e.Handled = true;

        var modifiers = new List<string>();
        if (Keyboard.Modifiers.HasFlag(ModifierKeys.Control)) modifiers.Add("Ctrl");
        if (Keyboard.Modifiers.HasFlag(ModifierKeys.Alt)) modifiers.Add("Alt");
        if (Keyboard.Modifiers.HasFlag(ModifierKeys.Shift)) modifiers.Add("Shift");
        if (Keyboard.Modifiers.HasFlag(ModifierKeys.Windows)) modifiers.Add("Win");

        var key = e.Key == Key.System ? e.SystemKey : e.Key;

        // Ignore modifier-only keys
        if (key == Key.LeftCtrl || key == Key.RightCtrl ||
            key == Key.LeftAlt || key == Key.RightAlt ||
            key == Key.LeftShift || key == Key.RightShift ||
            key == Key.LWin || key == Key.RWin)
        {
            return;
        }

        if (modifiers.Count == 0)
        {
            _activeHotkeyBox.Text = _activeHotkeyBox == OverlayHotkey ? _overlayHotkey : _memoHotkey;
            MessageBox.Show("修飾キー（Ctrl, Alt, Shift）と組み合わせてください。",
                "ホットキー設定", MessageBoxButton.OK, MessageBoxImage.Warning);
            _activeHotkeyBox = null;
            return;
        }

        var hotkeyString = string.Join("+", modifiers) + "+" + key.ToString();
        _activeHotkeyBox.Text = hotkeyString;

        if (_activeHotkeyBox == OverlayHotkey)
            _overlayHotkey = hotkeyString;
        else
            _memoHotkey = hotkeyString;

        _activeHotkeyBox = null;
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        MessageBox.Show($"ホットキーを保存しました。\n\n" +
            $"オーバーレイ: {OverlayHotkey.Text}\n" +
            $"メモ: {MemoHotkey.Text}\n\n" +
            "(変更は次回起動時に反映されます)",
            "ホットキー設定", MessageBoxButton.OK, MessageBoxImage.Information);
        Close();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        Close();
    }
}
