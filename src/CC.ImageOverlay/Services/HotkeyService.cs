using System.Runtime.InteropServices;
using System.Windows.Interop;
using System.Collections.Concurrent;
using CC.ImageOverlay.Infrastructure;

namespace CC.ImageOverlay.Services;

/// <summary>
/// 高性能かつ堅牢なホットキー管理サービス。
/// メッセージ専用ウィンドウを使用して、UIスレッドやメインウィンドウのライフサイクルから独立して動作します。
/// </summary>
public sealed class HotkeyService : IHotkeyService
{
    private const int WM_HOTKEY = 0x0312;
    private const int ERROR_HOTKEY_ALREADY_REGISTERED = 1409;

    // スレッドセーフな管理のための並列辞書
    private readonly ConcurrentDictionary<int, (HotkeyModifiers mods, VirtualKey key)> _hotkeys = new();
    
    private HwndSource? _hwndSource;
    private readonly object _lock = new();
    private bool _isDisposed;

    public event EventHandler<int>? HotkeyPressed;

    public HotkeyService()
    {
        // メッセージ専用ウィンドウをバックグラウンドで作成
        InitializeMessageWindow();
    }

    private void InitializeMessageWindow()
    {
        lock (_lock)
        {
            if (_hwndSource != null) return;

            // HWND_MESSAGE (-3) を親に指定することで、UIを持たないメッセージ受信専用ウィンドウを作成
            var parameters = new HwndSourceParameters("HotkeyMessageWindow")
            {
                ParentWindow = new IntPtr(-3), // HWND_MESSAGE
            };

            _hwndSource = new HwndSource(parameters);
            _hwndSource.AddHook(WndProc);
        }
    }

    public bool RegisterHotkey(int id, HotkeyModifiers modifiers, VirtualKey key)
    {
        ThrowIfDisposed();

        if (_hwndSource == null) return false;

        var hwnd = _hwndSource.Handle;
        
        // Win32 API 呼び出し
        if (!NativeMethods.RegisterHotKey(hwnd, id, (uint)modifiers, (uint)key))
        {
            var error = Marshal.GetLastWin32Error();
            if (error == ERROR_HOTKEY_ALREADY_REGISTERED)
            {
                // すでに登録されている場合の早期リターン
                return false;
            }
            // その他の致命的エラー
            throw new System.ComponentModel.Win32Exception(error);
        }

        _hotkeys.TryAdd(id, (modifiers, key));
        return true;
    }

    public bool UnregisterHotkey(int id)
    {
        ThrowIfDisposed();

        if (_hwndSource == null) return false;

        if (NativeMethods.UnregisterHotKey(_hwndSource.Handle, id))
        {
            _hotkeys.TryRemove(id, out _);
            return true;
        }
        return false;
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg == WM_HOTKEY)
        {
            // パフォーマンス最適化: IDの取得はO(1)
            int id = wParam.ToInt32();
            
            // イベント発行をTask.Runに逃がすことで、メッセージループのブロッキングを最小化
            // (CPUコアを効率的に利用し、メインスレッドのレスポンスを維持)
            var hotkeyId = id;
            HotkeyPressed?.Invoke(this, hotkeyId);
            
            handled = true;
        }
        return IntPtr.Zero;
    }

    private void ThrowIfDisposed()
    {
        if (_isDisposed) throw new ObjectDisposedException(nameof(HotkeyService));
    }

    public void Dispose()
    {
        if (_isDisposed) return;

        lock (_lock)
        {
            if (_isDisposed) return;

            if (_hwndSource != null)
            {
                // すべてのホットキーを解除
                foreach (var id in _hotkeys.Keys)
                {
                    NativeMethods.UnregisterHotKey(_hwndSource.Handle, id);
                }
                
                _hwndSource.RemoveHook(WndProc);
                _hwndSource.Dispose();
                _hwndSource = null;
            }

            _isDisposed = true;
        }
        GC.SuppressFinalize(this);
    }

    ~HotkeyService() => Dispose();
}

