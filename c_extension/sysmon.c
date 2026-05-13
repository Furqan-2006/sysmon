/*
 * sysmon.c — System Metrics Engine
 * Reads CPU, Memory, Disk, Process stats from Linux /proc filesystem
 * Compiled as a shared library (.so) and called from Python via ctypes
 */

#define _GNU_SOURCE

#include "sysmon.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <ctype.h>
#include <sys/statvfs.h>

// ─────────────────────────────────────────────
//  CPU — reads /proc/stat twice (100ms apart)
//  to compute real usage percentage
// ─────────────────────────────────────────────

typedef struct {
    long long user, nice, system, idle, iowait, irq, softirq, steal;
} RawCpu;

static RawCpu read_raw_cpu(void) {
    RawCpu r = {0};
    FILE *f = fopen("/proc/stat", "r");
    if (!f) return r;
    (void)fscanf(f, "cpu %lld %lld %lld %lld %lld %lld %lld %lld",
           &r.user, &r.nice, &r.system, &r.idle,
           &r.iowait, &r.irq, &r.softirq, &r.steal);
    fclose(f);
    return r;
}

CpuInfo get_cpu_info(void) {
    CpuInfo info = {0};

    RawCpu c1 = read_raw_cpu();
    usleep(100000); // 100ms sample window
    RawCpu c2 = read_raw_cpu();

    long long idle1  = c1.idle + c1.iowait;
    long long idle2  = c2.idle + c2.iowait;
    long long total1 = c1.user + c1.nice + c1.system + idle1 + c1.irq + c1.softirq + c1.steal;
    long long total2 = c2.user + c2.nice + c2.system + idle2 + c2.irq + c2.softirq + c2.steal;

    long long d_total = total2 - total1;
    long long d_idle  = idle2  - idle1;

    if (d_total == 0) return info;

    info.usage_percent = 100.0 * (double)(d_total - d_idle) / (double)d_total;
    info.user   = 100.0 * (double)(c2.user   - c1.user)   / (double)d_total;
    info.system = 100.0 * (double)(c2.system - c1.system) / (double)d_total;
    info.idle   = 100.0 * (double)d_idle / (double)d_total;
    return info;
}

// ─────────────────────────────────────────────
//  MEMORY — reads /proc/meminfo
// ─────────────────────────────────────────────

MemInfo get_mem_info(void) {
    MemInfo info = {0};
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return info;

    char key[64];
    long val;
    char unit[16];

    while (fscanf(f, "%63s %ld %15s\n", key, &val, unit) >= 2) {
        if      (strcmp(key, "MemTotal:")     == 0) info.total_kb     = val;
        else if (strcmp(key, "MemFree:")      == 0) info.free_kb      = val;
        else if (strcmp(key, "MemAvailable:") == 0) info.available_kb = val;
    }
    fclose(f);

    info.used_kb = info.total_kb - info.available_kb;
    if (info.total_kb > 0)
        info.usage_percent = 100.0 * (double)info.used_kb / (double)info.total_kb;
    return info;
}

// ─────────────────────────────────────────────
//  DISK — uses statvfs on root filesystem
// ─────────────────────────────────────────────

DiskInfo get_disk_info(void) {
    DiskInfo info = {0};
    struct statvfs s;

    if (statvfs("/", &s) != 0) return info;

    long block_kb     = s.f_bsize / 1024;
    info.total_kb     = (long)(s.f_blocks) * block_kb;
    info.free_kb      = (long)(s.f_bfree)  * block_kb;
    info.used_kb      = info.total_kb - info.free_kb;

    if (info.total_kb > 0)
        info.usage_percent = 100.0 * (double)info.used_kb / (double)info.total_kb;
    return info;
}

// ─────────────────────────────────────────────
//  PROCESSES — counts /proc/[pid]/status entries
// ─────────────────────────────────────────────

ProcessInfo get_process_info(void) {
    ProcessInfo info = {0};
    DIR *dir = opendir("/proc");
    if (!dir) return info;

    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        // only numeric entries are PIDs
        int is_pid = 1;
        for (char *c = entry->d_name; *c; c++) {
            if (!isdigit(*c)) { is_pid = 0; break; }
        }
        if (!is_pid) continue;
        info.total++;

        // read state from /proc/<pid>/stat
        char path[256];
        snprintf(path, sizeof(path), "/proc/%s/stat", entry->d_name);
        FILE *f = fopen(path, "r");
        if (!f) continue;

        char state = 0;
        int pid; char comm[256];
        (void)fscanf(f, "%d %255s %c", &pid, comm, &state);
        fclose(f);

        if (state == 'R') info.running++;
        else              info.sleeping++;
    }
    closedir(dir);
    return info;
}

// ─────────────────────────────────────────────
//  UPTIME — reads /proc/uptime
// ─────────────────────────────────────────────

double get_uptime_seconds(void) {
    double uptime = 0.0;
    FILE *f = fopen("/proc/uptime", "r");
    if (!f) return 0.0;
    (void)fscanf(f, "%lf", &uptime);
    fclose(f);
    return uptime;
}
