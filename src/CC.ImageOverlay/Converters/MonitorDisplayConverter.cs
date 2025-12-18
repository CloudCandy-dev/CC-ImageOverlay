using System;
using System.Globalization;
using System.Text.RegularExpressions;
using System.Windows.Data;
using CC.ImageOverlay.Models;
using CC.ImageOverlay.Services;
using Microsoft.Extensions.DependencyInjection;

namespace CC.ImageOverlay.Converters;

public partial class MonitorDisplayConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is not MonitorInfo monitor)
            return string.Empty;

        var languageService = App.Services.GetService<ILanguageService>();
        if (languageService == null)
            return monitor.ToString();

        var primaryText = languageService.GetText("ui_controls.monitor_display.primary", "Primary");
        var secondaryText = languageService.GetText("ui_controls.monitor_display.secondary", "Secondary");
        var format = languageService.GetText("ui_controls.monitor_display.format", "Monitor {0} ({1}) - {2}x{3}");
        
        // Extract monitor number from DeviceName
        var match = MonitorNumberRegex().Match(monitor.DeviceName);
        var monitorNumber = match.Success ? int.Parse(match.Value) : 0;
        
        var typeText = monitor.IsPrimary ? primaryText : secondaryText;

        try
        {
            return string.Format(format, monitorNumber, typeText, monitor.Width, monitor.Height);
        }
        catch (FormatException)
        {
            return monitor.ToString();
        }
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        throw new NotImplementedException();
    }

    [GeneratedRegex(@"\d+$")]
    private static partial Regex MonitorNumberRegex();
}
