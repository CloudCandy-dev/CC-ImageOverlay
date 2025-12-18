namespace CC.ImageOverlay.Services;

public interface ILanguageService
{
    string CurrentLanguage { get; }
    IReadOnlyDictionary<string, string> AvailableLanguages { get; }

    bool LoadLanguage(string languageCode);
    string GetText(string keyPath, string? defaultValue = null);

    event EventHandler<string>? LanguageChanged;
}
