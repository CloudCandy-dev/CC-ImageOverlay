using System.IO;
using System.Text.Json;

namespace CC.ImageOverlay.Services;

public class LanguageService : ILanguageService
{
    private readonly string _languagesDir;
    private readonly Dictionary<string, LanguageInfo> _languages = new();
    private JsonDocument? _currentData;

    public string CurrentLanguage { get; private set; } = "ja";

    public IReadOnlyDictionary<string, string> AvailableLanguages
        => _languages.ToDictionary(x => x.Key, x => x.Value.Name);

    public event EventHandler<string>? LanguageChanged;

    public LanguageService(string languagesDir = "Languages")
    {
        // Resolve absolute path
        _languagesDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, languagesDir);
        LoadAvailableLanguages();
        LoadLanguage(CurrentLanguage);
    }

    private void LoadAvailableLanguages()
    {
        if (!Directory.Exists(_languagesDir))
        {
            Directory.CreateDirectory(_languagesDir);
            return;
        }

        foreach (var file in Directory.GetFiles(_languagesDir, "*_v2.json"))
        {
            try
            {
                var json = File.ReadAllText(file);
                var doc = JsonDocument.Parse(json);
                var meta = doc.RootElement.GetProperty("meta");
                var code = meta.GetProperty("language_code").GetString()!;
                var name = meta.GetProperty("language_name").GetString()!;
                _languages[code] = new LanguageInfo(name, file, doc);
            }
            catch
            {
                // Skip invalid files
            }
        }
    }

    public bool LoadLanguage(string languageCode)
    {
        if (!_languages.TryGetValue(languageCode, out var info))
            return false;

        _currentData = info.Data;
        CurrentLanguage = languageCode;
        LanguageChanged?.Invoke(this, languageCode);
        return true;
    }

    public string GetText(string keyPath, string? defaultValue = null)
    {
        if (_currentData == null)
            return defaultValue ?? keyPath;

        try
        {
            var element = _currentData.RootElement;
            foreach (var key in keyPath.Split('.'))
            {
                if (!element.TryGetProperty(key, out element))
                    return defaultValue ?? keyPath;
            }
            return element.GetString() ?? defaultValue ?? keyPath;
        }
        catch
        {
            return defaultValue ?? keyPath;
        }
    }

    private record LanguageInfo(string Name, string FilePath, JsonDocument Data);
}
