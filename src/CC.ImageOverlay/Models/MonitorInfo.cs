using System.Windows;
using System.Text.RegularExpressions;

namespace CC.ImageOverlay.Models;

/// <summary>
/// モニター情報
/// </summary>
public partial record MonitorInfo
{
    public required IntPtr Handle { get; init; }
    public required string DeviceName { get; init; }
    public required Rect Bounds { get; init; }
    public required bool IsPrimary { get; init; }

    public int Width => (int)Bounds.Width;
    public int Height => (int)Bounds.Height;
    public int Left => (int)Bounds.X;
    public int Top => (int)Bounds.Y;

    /// <summary>
    /// ディスプレイ番号を取得（例: \\.\DISPLAY1 → 1）
    /// </summary>
    private int MonitorNumber => 
        int.TryParse(MonitorNumberRegex().Match(DeviceName).Value, out var num) ? num : 0;

    public string DisplayName => IsPrimary
        ? $"モニター {MonitorNumber} (メイン) - {Width}×{Height}"
        : $"モニター {MonitorNumber} (サブ) - {Width}×{Height}";

    public override string ToString() => DisplayName;

    [GeneratedRegex(@"\d+$")]
    private static partial Regex MonitorNumberRegex();
}
