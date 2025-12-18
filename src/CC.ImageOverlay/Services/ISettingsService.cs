using CC.ImageOverlay.Models;

namespace CC.ImageOverlay.Services;

public interface ISettingsService
{
    AppSettings CurrentSettings { get; }
    void Load();
    void Save();
    void UpdateLanguage(string language);
    void UpdateTheme(string theme);
}
