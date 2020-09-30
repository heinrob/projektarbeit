#!/bin/bash
while true; do
    hcitool -i hci0 cmd 0x08 0x0008 1E 02 01 1A 1A FF 4C 00 02 15 FF FF FF FF FF FF FF FF FF FF FF FF `printf '%x' $(date +%s) | sed 's/.\{2\}/& /g'` 00 00 00 00 C8 00
    sleep 1
done
