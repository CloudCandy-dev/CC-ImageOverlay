using System.Windows.Media;
using CC.ImageOverlay.Models;
using CC.ImageOverlay.Views;

namespace CC.ImageOverlay.Services;

public class OverlayService : IOverlayService
{
    private OverlayWindow? _overlayWindow;
    private MonitorInfo? _currentMonitor;

    public bool IsVisible => _overlayWindow?.IsVisible ?? false;

    public void ShowImageOverlay(string imagePath, double opacity, int width, int height, int x, int y, MonitorInfo monitor)
    {
        EnsureWindow();
        _currentMonitor = monitor;
        UpdateImageOverlay(imagePath, opacity, width, height, x, y, monitor);
        _overlayWindow!.Show();
    }

    public void UpdateImageOverlay(string imagePath, double opacity, int width, int height, int x, int y, MonitorInfo monitor)
    {
        if (_overlayWindow == null) return;
        _currentMonitor = monitor;
        _overlayWindow.SetImageWithSize(imagePath, opacity, width, height);
        UpdatePosition(x, y, monitor);
    }

    public void ShowMemoOverlay(string text, string fontFamily, double fontSize,
        Color textColor, double textOpacity,
        Color bgColor, double bgOpacity,
        int width, int height, int x, int y, MonitorInfo monitor)
    {
        EnsureWindow();
        _currentMonitor = monitor;
        UpdateMemoOverlay(text, fontFamily, fontSize, textColor, textOpacity, bgColor, bgOpacity, width, height, x, y, monitor);
        _overlayWindow!.Show();
    }

    public void UpdateMemoOverlay(string text, string fontFamily, double fontSize,
        Color textColor, double textOpacity,
        Color bgColor, double bgOpacity,
        int width, int height, int x, int y, MonitorInfo monitor)
    {
        if (_overlayWindow == null) return;
        _currentMonitor = monitor;
        _overlayWindow.SetMemo(text, fontFamily, fontSize, textColor, textOpacity, bgColor, bgOpacity, width, height);
        UpdatePosition(x, y, monitor);
    }

    public void Hide()
    {
        _overlayWindow?.Hide();
    }

    public void UpdatePosition(int x, int y, MonitorInfo monitor)
    {
        if (_overlayWindow == null) return;
        _currentMonitor = monitor;
        _overlayWindow.SetPosition(x + (int)monitor.Bounds.Left, y + (int)monitor.Bounds.Top);
    }

    public void SetClickThrough(bool enable)
    {
        _overlayWindow?.SetClickThrough(enable);
    }

    public void Close()
    {
        _overlayWindow?.Close();
        _overlayWindow = null;
    }

    private void EnsureWindow()
    {
        if (_overlayWindow == null)
        {
            _overlayWindow = new OverlayWindow();
        }
    }
}
