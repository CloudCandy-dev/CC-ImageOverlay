using CC.ImageOverlay.Models;
using CC.ImageOverlay.Views;

namespace CC.ImageOverlay.Services;

public interface IOverlayService
{
    bool IsVisible { get; }
    void ShowImageOverlay(string imagePath, double opacity, int width, int height, int x, int y, MonitorInfo monitor);
    void UpdateImageOverlay(string imagePath, double opacity, int width, int height, int x, int y, MonitorInfo monitor);
    
    void ShowMemoOverlay(string text, string fontFamily, double fontSize, 
        System.Windows.Media.Color textColor, double textOpacity,
        System.Windows.Media.Color bgColor, double bgOpacity,
        int width, int height, int x, int y, MonitorInfo monitor);
    void UpdateMemoOverlay(string text, string fontFamily, double fontSize, 
        System.Windows.Media.Color textColor, double textOpacity,
        System.Windows.Media.Color bgColor, double bgOpacity,
        int width, int height, int x, int y, MonitorInfo monitor);
        
    void Hide();
    void UpdatePosition(int x, int y, MonitorInfo monitor);
    void SetClickThrough(bool enable);
    void Close();
}
