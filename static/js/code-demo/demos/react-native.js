Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait;
    var p = Promise.resolve();

    E.setFilename('MeterReader.tsx');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _("import React, { useState, useEffect } from 'react'", E.speeds.m); }).then(n);
    p = p.then(function() { return _("import { View, Text, Button, FlatList } from 'react-native'", E.speeds.m); }).then(n);
    p = p.then(function() { return _("import NfcManager from 'react-native-nfc-manager'", E.speeds.m); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('interface MeterReading {', E.speeds.m); }).then(n);
    p = p.then(function() { return _('  id: number', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  customerId: number', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  reading: number', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  timestamp: string', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  synced: boolean', E.speeds.s); }).then(n);
    p = p.then(function() { return _('}', E.speeds.s); }).then(n);
    p = p.then(function() { return w(150); });
    p = p.then(n);

    p = p.then(function() { return _('export default function MeterReader() {', E.speeds.m); }).then(n);
    p = p.then(function() { return _('  const [readings, setReadings] = useState<MeterReading[]>([])', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  const [isScanning, setIsScanning] = useState(false)', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('  async function scanNfcTag() {', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    setIsScanning(true)', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    await NfcManager.registerTagEvent()', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    const tag = await NfcManager.getTag()', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    console.log("Tag detected:", tag.id)', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    setIsScanning(false)', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  }', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('  return (', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    <View style={{ flex: 1, padding: 16 }}>', E.speeds.s); }).then(n);
    p = p.then(function() { return _('      <Text style={{ fontSize: 20 }}>Meter Reader</Text>', E.speeds.s); }).then(n);
    p = p.then(function() { return _('      <Button', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        title={isScanning ? "Scanning..." : "Scan NFC"}', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        onPress={scanNfcTag}', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        disabled={isScanning}', E.speeds.s); }).then(n);
    p = p.then(function() { return _('      />', E.speeds.s); }).then(n);
    p = p.then(function() { return _('      <FlatList', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        data={readings}', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        renderItem={({ item }) => (', E.speeds.s); }).then(n);
    p = p.then(function() { return _('          <Text>{item.customerId}: {item.reading}</Text>', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        )}', E.speeds.s); }).then(n);
    p = p.then(function() { return _('      />', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    </View>', E.speeds.s); }).then(n);
    p = p.then(function() { return _('  )', E.speeds.s); }).then(n);
    p = p.then(function() { return _('}', E.speeds.m); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ npx expo start', color: 'var(--accent)', delay: 400 },
        { text: '', delay: 60 },
        { text: 'Starting Metro Bundler...', color: 'var(--text-secondary)', delay: 500 },
        { text: ' › Metro waiting on exp://192.168.1.100:8081', color: '#50fa7b', delay: 400 },
        { text: ' › Scan QR code with Expo Go', color: 'var(--text-secondary)', delay: 200 },
        { text: '', delay: 60 },
        { text: ' LOG  Tag detected: 04:5A:2B:1C:8F:00', color: '#8be9fd', delay: 600 },
        { text: ' ✓ NFC reading stored locally · 14 unsynced', color: '#f1fa8c', delay: 300 },
    ]); });

    return p;
});
