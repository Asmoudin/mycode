import React, { useState, useEffect } from 'react';
import { View, Text, Button, FlatList } from 'react-native';
import BleManager from 'react-native-ble-manager';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BluetoothScanner = () => {
    const [devices, setDevices] = useState([]);
    const [token, setToken] = useState('');

    useEffect(() => {
        BleManager.start({ showAlert: false });

        AsyncStorage.getItem('token').then(token => setToken(token));

        BleManager.scan([], 5, true).then(() => {
            console.log('Scanning...');
        });

        BleManager.on('BleManagerDiscoverPeripheral', handleDiscoverPeripheral);
    }, []);

    const handleDiscoverPeripheral = (peripheral) => {
        setDevices((prevDevices) => [...prevDevices, peripheral]);
    };

    const sendDevicesToBackend = async () => {
        try {
            const nearbyDevices = devices.map(device => device.name);
            const response = await axios.post('http://localhost:5000/nearby-users',
                { nearbyDevices },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            console.log('Nearby Users:', response.data.nearbyUsers);
        } catch (error) {
            console.error('Error communicating with backend:', error);
        }
    };

    return (
        <View>
            <Button title="Start Scan" onPress={() => BleManager.scan([], 5, true)} />
            <FlatList
                data={devices}
                renderItem={({ item }) => <Text>{item.name || 'Unnamed Device'}</Text>}
                keyExtractor={(item) => item.id}
            />
            <Button title="Send Devices to Backend" onPress={sendDevicesToBackend} />
        </View>
    );
};

export default BluetoothScanner;
