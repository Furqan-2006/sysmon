#ifndef SYSMON_H
#define SYSMON_H

// ─────────────────────────────────────────────
//  SysMon C Extension – Data Structures
// ─────────────────────────────────────────────

typedef struct {
    double user;
    double system;
    double idle;
    double usage_percent;
} CpuInfo;

typedef struct {
    long total_kb;
    long used_kb;
    long free_kb;
    long available_kb;
    double usage_percent;
} MemInfo;

typedef struct {
    long total_kb;
    long used_kb;
    long free_kb;
    double usage_percent;
} DiskInfo;

typedef struct {
    int total;
    int running;
    int sleeping;
} ProcessInfo;

// ─────────────────────────────────────────────
//  Exported Functions (called via ctypes)
// ─────────────────────────────────────────────

CpuInfo  get_cpu_info(void);
MemInfo  get_mem_info(void);
DiskInfo get_disk_info(void);
ProcessInfo get_process_info(void);
double   get_uptime_seconds(void);

#endif // SYSMON_H
