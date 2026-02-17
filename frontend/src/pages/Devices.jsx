import { useEffect, useState } from "react";
import { devices } from "../services/api";
import { Activity, Battery, MapPin } from "lucide-react";
import React from 'react';

const DeviceList = () => {
    const [list, setList] = useState([]);

    useEffect(() => {
        devices.list().then(res => setList(res.data.data.items));
    }, []);

    return (
        <div className="flex flex-col gap-6">
            <h1>Connected Devices</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {list.map(device => (
                    <div key={device.id} className="card hover:border-accent-primary transition-all">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="font-bold">{device.name}</h3>
                                <div className="text-secondary text-sm flex items-center gap-1">
                                    <MapPin size={14} /> {device.location}
                                </div>
                            </div>
                            <span className={`badge ${device.status === 'active' ? 'badge-active' : 'badge-inactive'}`}>
                                {device.status}
                            </span>
                        </div>

                        <div className="flex gap-4 border-t border-border-color pt-4 mt-2">
                            <div className="flex-1 text-center">
                                <small>Type</small>
                                <div className="font-medium">{device.type}</div>
                            </div>
                            <div className="flex-1 text-center border-l border-border-color">
                                <small>Last Seen</small>
                                <div className="font-medium">
                                    {new Date(device.last_seen_at).toLocaleTimeString()}
                                </div>
                            </div>
                        </div>

                        <div className="mt-4 flex justify-end">
                            <button className="btn btn-outline text-sm w-full">View Telemetry</button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DeviceList;
