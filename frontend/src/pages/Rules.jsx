import { useEffect, useState } from "react";
import { rules } from "../services/api";
import { Plus, Trash2, Edit } from "lucide-react";
import React from 'react';

const RuleList = () => {
    const [list, setList] = useState([]);

    useEffect(() => {
        rules.list().then(res => setList(res.data.data.items));
    }, []);

    const handleDelete = (id) => {
        if (confirm("Delete this rule?")) {
            rules.delete(id).then(() => setList(list.filter(i => i.id !== id)));
        }
    };

    return (
        <div className="card w-full">
            <div className="flex justify-between items-center mb-6">
                <h1>Active Rules</h1>
                <button className="btn btn-primary text-sm flex gap-2">
                    <Plus size={16} /> New Rule
                </button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Device</th>
                        <th>Condition</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {list.map(rule => (
                        <tr key={rule.id}>
                            <td className="font-medium">{rule.name}</td>
                            <td className="text-secondary">{rule.device_id}</td>
                            <td>
                                <span className="badge font-mono border border-border-color">
                                    {rule.conditions[0]?.property} {rule.conditions[0]?.operator} {rule.conditions[0]?.threshold}
                                </span>
                                {rule.conditions.length > 1 && <span className="text-xs ml-2 text-secondary">+{rule.conditions.length - 1}</span>}
                            </td>
                            <td>
                                <span className={`badge ${rule.is_active ? 'badge-active' : 'badge-inactive'}`}>
                                    {rule.is_active ? 'Active' : 'Paused'}
                                </span>
                            </td>
                            <td>
                                <div className="flex gap-2">
                                    <button className="text-secondary hover:text-accent-primary" title="Edit">
                                        <Edit size={16} />
                                    </button>
                                    <button onClick={() => handleDelete(rule.id)} className="text-secondary hover:text-danger" title="Delete">
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {list.length === 0 && (
                <div className="p-8 text-center text-secondary">
                    No rules configured. Start monitoring by creating a new rule.
                </div>
            )}
        </div>
    );
};

export default RuleList;
