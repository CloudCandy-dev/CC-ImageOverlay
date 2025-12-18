using System.Runtime.InteropServices;
using System.Windows;
using CC.ImageOverlay.Models;
using CC.ImageOverlay.Infrastructure;

namespace CC.ImageOverlay.Services;

public class MonitorService : IMonitorService
{
    public IEnumerable<MonitorInfo> GetMonitors()
    {
        var monitors = new List<MonitorInfo>();

        NativeMethods.EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero,
            delegate(IntPtr hMonitor, IntPtr hdcMonitor, ref NativeMethods.RECT lprcMonitor, IntPtr dwData)
            {
                var info = new NativeMethods.MONITORINFOEX();
                info.cbSize = Marshal.SizeOf(info);

                if (NativeMethods.GetMonitorInfo(hMonitor, ref info))
                {
                    monitors.Add(new MonitorInfo
                    {
                        Handle = hMonitor,
                        DeviceName = info.szDevice,
                        Bounds = new Rect(
                            info.rcMonitor.Left,
                            info.rcMonitor.Top,
                            info.rcMonitor.Right - info.rcMonitor.Left,
                            info.rcMonitor.Bottom - info.rcMonitor.Top),
                        IsPrimary = (info.dwFlags & 1) != 0
                    });
                }
                return true;
            }, IntPtr.Zero);

        return monitors;
    }

    public MonitorInfo? GetPrimaryMonitor()
        => GetMonitors().FirstOrDefault(m => m.IsPrimary);

    public MonitorInfo? GetMonitorByDeviceName(string deviceName)
        => GetMonitors().FirstOrDefault(m => m.DeviceName == deviceName);
}
