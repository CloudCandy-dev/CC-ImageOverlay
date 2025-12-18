using System.Globalization;
using System.Windows.Data;

namespace CC.ImageOverlay.Converters;

public class IntToBoolConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is int intValue && parameter is string paramString && int.TryParse(paramString, out int targetValue))
        {
            return intValue == targetValue;
        }
        return false;
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
    {
        if (value is bool boolValue && boolValue && parameter is string paramString && int.TryParse(paramString, out int targetValue))
        {
            return targetValue;
        }
        return Binding.DoNothing;
    }
}
