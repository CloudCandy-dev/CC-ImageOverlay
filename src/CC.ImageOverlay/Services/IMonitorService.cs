using CC.ImageOverlay.Models;

namespace CC.ImageOverlay.Services;

public interface IMonitorService
{
    IEnumerable<MonitorInfo> GetMonitors();
    MonitorInfo? GetPrimaryMonitor();
    MonitorInfo? GetMonitorByDeviceName(string deviceName);
}
