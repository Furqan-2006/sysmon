# ─────────────────────────────────────────────
#  SysMon C Extension – Makefile
# ─────────────────────────────────────────────

CC      = gcc
CFLAGS  = -O2 -Wall -Wextra -fPIC -std=c99 -Wno-unused-result -Wno-format-truncation
TARGET  = sysmon.so
SRC     = sysmon.c

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRC) sysmon.h
	$(CC) $(CFLAGS) -shared -o $(TARGET) $(SRC)
	@echo "✅ Built $(TARGET) successfully"

clean:
	rm -f $(TARGET)
	@echo "🧹 Cleaned build artifacts"
