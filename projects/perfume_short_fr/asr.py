import sherpa_onnx, numpy as np, wave, json
M="models/sherpa-onnx-whisper-medium/medium-"
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+"encoder.int8.onnx",decoder=M+"decoder.int8.onnx",tokens=M+"tokens.txt",num_threads=4,language="fr",task="transcribe")
w=wave.open("audio16.wav");a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
cfg=sherpa_onnx.VadModelConfig();cfg.silero_vad.model="models/silero_vad.onnx";cfg.silero_vad.min_silence_duration=0.25;cfg.silero_vad.max_speech_duration=4;cfg.silero_vad.threshold=0.4;cfg.sample_rate=16000
vad=sherpa_onnx.VoiceActivityDetector(cfg,buffer_size_in_seconds=120)
segs=[]
for i in range(0,len(a),512):
    vad.accept_waveform(a[i:i+512])
    while not vad.empty():
        segs.append((vad.front.start,np.array(vad.front.samples)));vad.pop()
vad.flush()
while not vad.empty(): segs.append((vad.front.start,np.array(vad.front.samples)));vad.pop()
out=[]
for st,s in segs:
    x=rec.create_stream();x.accept_waveform(16000,s);rec.decode_stream(x)
    t0=st/16000;t1=t0+len(s)/16000;txt=x.result.text.strip()
    print(f"[{t0:6.2f}-{t1:6.2f}] ({x.result.lang}) {txt}",flush=True)
    out.append({"start":t0,"end":t1,"text":txt})
json.dump(out,open("segments.json","w"),indent=1)
