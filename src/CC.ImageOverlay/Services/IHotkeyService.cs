namespace CC.ImageOverlay.Services;

public interface IHotkeyService : IDisposable
{
    bool RegisterHotkey(int id, HotkeyModifiers modifiers, VirtualKey key);
    bool UnregisterHotkey(int id);
    
    event EventHandler<int>? HotkeyPressed;
}

[Flags]
public enum HotkeyModifiers : uint
{
    None = 0x0000,
    Alt = 0x0001,
    Control = 0x0002,
    Shift = 0x0004,
    Win = 0x0008,
    NoRepeat = 0x4000 // RegisterHotKey modifiers can include MOD_NOREPEAT
}

/// <summary>
/// Virtual Key Codes (Selection)
/// </summary>
public enum VirtualKey : uint
{
    O = 0x4F,  // 'O' key
    M = 0x4D,  // 'M' key
    H = 0x48,  // 'H' key
    F1 = 0x70,
    F2 = 0x71,
    F3 = 0x72,
    F4 = 0x73,
    // Add more as needed or use a comprehensive enum
}
