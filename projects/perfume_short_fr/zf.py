import sherpa_onnx, numpy as np, wave, json
D="models/sherpa-onnx-streaming-zipformer-fr-2023-04-14/"
r=sherpa_onnx.OnlineRecognizer.from_transducer(tokens=D+"tokens.txt",encoder=D+"encoder-epoch-29-avg-9-with-averaged-model.int8.onnx",decoder=D+"decoder-epoch-29-avg-9-with-averaged-model.int8.onnx",joiner=D+"joiner-epoch-29-avg-9-with-averaged-model.int8.onnx",num_threads=4,sample_rate=16000,feature_dim=80)
w=wave.open("audio16.wav");a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
s=r.create_stream();s.accept_waveform(16000,np.concatenate([a,np.zeros(16000,np.float32)]));s.input_finished()
while r.is_ready(s): r.decode_stream(s)

import json as J; res=J.loads(r.get_result_as_json_string(s))
toks=res["tokens"];ts=res["timestamps"]
words=[];
for t,tt in zip(toks,ts):
    if t[:1] in ("▁"," ") or not words: words.append({"w":t.lstrip("▁ "),"s":tt})
    else: words[-1]["w"]+=t
json.dump(words,open("zf_words.json","w"))
print(" ".join(f"{x['w']}@{x['s']:.1f}" for x in words))
