namespace CC.ImageOverlay.Models;

/// <summary>
/// オーバーレイの設定
/// </summary>
public record OverlaySettings
{
    public string? ImagePath { get; init; }
    public int PositionX { get; init; }
    public int PositionY { get; init; }
    public double Opacity { get; init; } = 0.8;
    public double Scale { get; init; } = 1.0;
    public string MonitorId { get; init; } = "";
    public bool IsClickThrough { get; init; } = true;
}

/// <summary>
/// メモの設定
/// </summary>
public record MemoSettings
{
    public string Text { get; init; } = "";
    public string FontFamily { get; init; } = "Noto Sans JP";
    public double FontSize { get; init; } = 14;
    public string TextColor { get; init; } = "#FFFFFF";
    public double TextOpacity { get; init; } = 1.0;
    public string BackgroundColor { get; init; } = "#000000";
    public double BackgroundOpacity { get; init; } = 0.78;
    public int PositionX { get; init; }
    public int PositionY { get; init; }
    public double Scale { get; init; } = 1.0;
    public string MonitorId { get; init; } = "";
}

/// <summary>
/// アプリケーション設定
/// </summary>
public record AppSettings
{
    public string Language { get; init; } = "ja";
    public string Theme { get; init; } = "Dark";
    public OverlaySettings? LastOverlaySettings { get; init; }
    public MemoSettings? LastMemoSettings { get; init; }
}
