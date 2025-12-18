using System.IO;
using System.Text.Json;
using CC.ImageOverlay.Models;

namespace CC.ImageOverlay.Services;

public class SettingsService : ISettingsService
{
    private static readonly string SettingsDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "CC-ImageOverlay");
    private static readonly string SettingsPath = Path.Combine(SettingsDir, "settings.json");
    
    private readonly JsonSerializerOptions _jsonOptions = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    public AppSettings CurrentSettings { get; private set; } = new();

    public void Load()
    {
        try
        {
            if (File.Exists(SettingsPath))
            {
                var json = File.ReadAllText(SettingsPath);
                CurrentSettings = JsonSerializer.Deserialize<AppSettings>(json, _jsonOptions)
                    ?? new AppSettings();
            }
        }
        catch
        {
            CurrentSettings = new AppSettings();
        }
    }

    public void Save()
    {
        try
        {
            // Ensure directory exists
            if (!Directory.Exists(SettingsDir))
            {
                Directory.CreateDirectory(SettingsDir);
            }

            var json = JsonSerializer.Serialize(CurrentSettings, _jsonOptions);
            File.WriteAllText(SettingsPath, json);
        }
        catch
        {
            // Log error
        }
    }

    public void UpdateLanguage(string language)
    {
        CurrentSettings = CurrentSettings with { Language = language };
        Save();
    }

    public void UpdateTheme(string theme)
    {
        CurrentSettings = CurrentSettings with { Theme = theme };
        Save();
    }
}
