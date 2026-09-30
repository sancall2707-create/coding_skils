import { useState, useRef, useEffect } from 'react';
import { Clock, X } from 'lucide-react';

export default function TimePicker({ label, value, onChange }) {
  const [open, setOpen] = useState(false);
  const [hour, setHour] = useState(value ? value.split(':')[0] : '08');
  const [minute, setMinute] = useState(value ? value.split(':')[1] : '00');

  const hourListRef = useRef(null);
  const minuteListRef = useRef(null);

  const save = () => {
    onChange(`${hour}:${minute}`);
    setOpen(false);
  };

  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
  const minutes = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

  useEffect(() => {
    if (open) {
      setTimeout(() => {
        const selectedHourEl = hourListRef.current?.querySelector('[data-selected="true"]');
        const selectedMinEl = minuteListRef.current?.querySelector('[data-selected="true"]');
        selectedHourEl?.scrollIntoView({ block: 'center' });
        selectedMinEl?.scrollIntoView({ block: 'center' });
      }, 50);
    }
  }, [open]);

  return (
    <div>
      {label && <label className="block text-xs font-semibold text-slate-700 mb-1.5">{label}</label>}
      <button
        type="button"
        onClick={() => {
          if (value) {
            const [h, m] = value.split(':');
            if (h) setHour(h);
            if (m) setMinute(m);
          }
          setOpen(true);
        }}
        className="w-full flex items-center justify-between border border-slate-300 rounded-xl px-3.5 py-2.5 text-left text-sm bg-white hover:border-[#0F2C59] transition-colors cursor-pointer"
      >
        <span className={value ? 'font-bold text-slate-900' : 'text-slate-400'}>
          {value || 'Pilih Jam'}
        </span>
        <Clock size={18} className="text-slate-400" />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="bg-white w-full sm:max-w-xs rounded-t-2xl sm:rounded-2xl p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-[#0F2C59]">{label || 'Pilih Waktu'}</h3>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-extrabold text-slate-500 block mb-1">JAM (00–23)</label>
                <div ref={hourListRef} className="h-44 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100 bg-white">
                  {hours.map(h => (
                    <button
                      key={h}
                      type="button"
                      data-selected={hour === h}
                      onClick={() => setHour(h)}
                      className={`w-full py-2 text-center font-bold text-sm transition-colors ${
                        hour === h ? 'bg-[#0F2C59] text-white' : 'hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      {h}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-extrabold text-slate-500 block mb-1">MENIT (00–59)</label>
                <div ref={minuteListRef} className="h-44 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100 bg-white">
                  {minutes.map(m => (
                    <button
                      key={m}
                      type="button"
                      data-selected={minute === m}
                      onClick={() => setMinute(m)}
                      className={`w-full py-2 text-center font-bold text-sm transition-colors ${
                        minute === m ? 'bg-[#0F2C59] text-white' : 'hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={save}
                className="w-full py-3 bg-[#0F2C59] text-white font-extrabold rounded-xl shadow-md hover:bg-[#123A75] transition-colors"
              >
                Terapkan ({hour}:{minute})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
