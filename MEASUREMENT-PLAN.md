# แผนการวัดวัตถุประสงค์ — งานที่เหลือ

ปรับปรุง 24 ก.ย. 19:30 · แทนฉบับเดิมทั้งหมด · ข้อ 2 และข้อ 3 เสร็จแล้ว เหลือ B → C → D → E → โต๊ะ

---

## 0. ภาพรวม

| ข้อ | วัดอะไร | เกณฑ์ | สถานะ | ต้องทำ | รอบ |
|---|---|---|---|---|---|
| 1 | ความคลาดเคลื่อนตำแหน่งหุ่นบนแผนที่ | ≤ 10 ซม. | ❌ ผลเก่าไม่ผ่าน (ALIGNED 42.4 ซม. ไฟล์ปนหลาย session) | วัดใหม่ทั้งชุด | **D** |
| 2 | ความแม่นยำการตรวจจับ (macro F1) | ≥ 80% | ✅ **82.2%** yolo26l TensorRT conf 0.4 (เดิม 64.4%) · ปรับบนชุดเดียวกัน D-29 | — ใส่รายงานแล้ว | — |
| 3 | ความเร็วตรวจจับขณะ SLAM ทำงาน | ≥ 5 FPS | ✅ **15.16 FPS** yolo26l TensorRT + SLAM + semantic | — ใส่รายงานแล้ว | — |
| 4 | ความคลาดเคลื่อนตำแหน่งวัตถุบนแผนที่ | ≤ 50 ซม. | 🟡 8 ซม. จากจุดเดียว | วัด 4 ด้านรอบเก้าอี้ | **B** |
| 5 | CPU เฉลี่ยขณะทำงานเต็มระบบ | ≤ 80% | ⬜ ยังไม่วัด (ผลเก่า 76–81% เป็นของ yolo26s) | วัดด้วย yolo26l ขณะขับ | **C** |

| รอบ | ใช้วัด | `real` | `slam` | `yolo` | `semantic` | `nav` | `bag` | เวลา |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|---|
| **B** | ข้อ 4 + แคปรูป 3 รูป | ✅ | ✅ | ✅ | ✅ | | | 20 นาที |
| **C** | ข้อ 5 | ✅ | ✅ | ✅ | ✅ | | ❌ ห้าม | 10 นาที |
| **D** | ข้อ 1 | ✅ | ✅ | | | | | 40 นาที |
| **E** | รูป Nav2 | ✅ | | | | ✅ | | 5 นาที |

**B กับ C ต่อกันได้เลย** — ใช้ชุดเดียวกัน · D ต้อง**ปิด slam แล้วเปิดใหม่** (origin ต้องตั้งที่ HOME) · E ห้ามเปิด slam

---

## 1. วิธีเปิดระบบ (B และ C)

> ✅ **`make yolo` เปล่า ๆ = yolo26l TensorRT 480×640 conf 0.4 แล้ว** (D-30) ตรงกับที่รายงานเขียนไว้
> ถ้าไฟล์ engine หาย (เช่นหลังเปลี่ยน JetPack) `make yolo` จะ build ให้เอง ~13 นาที
> — ต้อง**ปิดระบบก่อน** ถ้า RAM ว่างไม่ถึง 4.5 GB สคริปต์จะไม่ยอม build
> ตัวเก่า: `make yolo MODEL=$HOME/yolo/yolo26s.onnx CONF=0.5`

เปิดทีละ terminal ตามลำดับ รอให้ตัวก่อนหน้าขึ้นครบก่อน:

| คำสั่ง | รอจนเห็น |
|---|---|
| `cd ~/cap_ws && make real` | `Configured and activated diff_cont` · lidar `Lidar has started!` (checksum error ตอนเปิดไม่กี่บรรทัดเป็นเรื่องปกติ) |
| `make slam` | `Registering sensor` |
| `make yolo` | `imgsz [480, 640] (from the model)` · `conf 0.4` · `15.x Hz` |
| `make semantic` | `fused .../... detections` |
| `make teleop SPEED=0.10` | ใช้ขับหุ่น |

**ตอนนี้ (24 ก.ย. 19:10) ระบบเปิดค้างไว้ใน tmux session `meas`** — real · slam · semantic · yolo (L engine, conf 0.4)
ดูด้วย `tmux attach -t meas` (`Ctrl-b n` สลับหน้าต่าง · `Ctrl-b d` ออกโดยไม่ปิด) · เหลือเปิดแค่ teleop
ถ้าเปิดใหม่เองแล้ว ให้ปิดของใน `meas` ก่อน (`tmux kill-session -t meas` หลัง Ctrl-C ทุกหน้าต่าง)

ทุก terminal ที่พิมพ์ `ros2 run` ต้อง source ก่อน:
```bash
source /opt/ros/humble/setup.bash && source ~/cap_ws/install/setup.bash
```

---

## 2. รอบ B — ข้อ 4 วัดตำแหน่งเก้าอี้ 4 ด้าน

**เช็กก่อนเริ่ม** (ไม่มีข้อมูล / error = อย่าเพิ่งวัด ย้อนดูว่า terminal ไหนตาย):
```bash
ros2 topic echo --once /semantic_landmarks | head -5
ros2 run tf2_ros tf2_echo map base_footprint
```
(`ros2 topic hz` กับ topic ที่เป็น best-effort จะเงียบ ไม่ได้แปลว่าตาย — ใช้ `echo --once` แทน)

### 2.1 วัดตลับเมตร 2 ค่า

```
                    วัตถุ (เก้าอี้)
                      ●
                      |
                      |  ← left = ระยะตั้งฉาก
                      |    (ซ้าย = บวก, ขวา = ลบ)
      [หุ่นยนต์]------+------------→ แนวกึ่งกลางลำตัว
        ▲
    กึ่งกลางเพลาล้อ
        |←─ fwd ─→|
```

- **`--fwd`** วัดตามแนวกึ่งกลางลำตัว จาก**กึ่งกลางเพลาล้อ** (ไม่ใช่หัวหุ่น)
- **`--left`** วัดตั้งฉากออกไปหาวัตถุ · ซ้าย = บวก · **ขวา = ลบ**
- หาแนวกึ่งกลางด้วยเชือกทาบ อย่ากะด้วยตา (เอียง 3° ที่ 1.5 ม. = คลาด 8 ซม.)
- ถ้าวัตถุเฉียงมาก วัดระยะตรง `d` กับมุม `θ` แล้วคิด `fwd = d·cosθ`, `left = d·sinθ`

### 2.2 วัด 4 ด้าน

**ห้ามขยับเก้าอี้ตลอดรอบนี้** · วัดด้าน `front` ใหม่ด้วย ให้ทั้ง 4 ค่ามาจากสคริปต์และวิธีเดียวกัน

| ด้าน | จอดยังไง | `--pass-label` |
|---|---|---|
| 1 | หน้าเก้าอี้ ห่าง ~1.5 ม. หันเข้าหา | `front` |
| 2 | อ้อมไปด้านขวา หันเข้าหา | `right` |
| 3 | อ้อมไปด้านหลัง หันเข้าหา | `back` |
| 4 | อ้อมไปด้านซ้าย หันเข้าหา | `left` |

**แต่ละด้าน:** จอด → รอนิ่ง 3 วินาที → วัดตลับเมตร → เช็กว่า yolo เห็นเก้าอี้ → รันคำสั่ง → **ห้ามขยับหุ่น 30 วินาที**

```bash
ros2 run my_bot object_accuracy.py chair --fwd <ค่าจริง> --left <ค่าจริง> --pass-label front
ros2 run my_bot object_accuracy.py chair --fwd <ค่าจริง> --left <ค่าจริง> --pass-label right
ros2 run my_bot object_accuracy.py chair --fwd <ค่าจริง> --left <ค่าจริง> --pass-label back
ros2 run my_bot object_accuracy.py chair --fwd <ค่าจริง> --left <ค่าจริง> --pass-label left
ros2 run my_bot object_accuracy.py chair --summary
```

### 2.3 อ่านผล

แต่ละด้านดู 2 บรรทัด: **`ERROR` ≤ 50 ซม.** · **`spread`** ยิ่งน้อยยิ่งดี

| `--summary` บอกว่า | แปลว่า | เขียนในรายงาน |
|---|---|---|
| **CONVERGENCE** (id เดิม) | วัตถุชิ้นเดิม ตำแหน่งปรับเข้าที่ | ผสานข้อมูลข้ามมุมมองได้จริง |
| **VIEWPOINT DEPENDENCE** (id เปลี่ยน) | ระบบสร้างวัตถุใหม่แทนการผสาน | ข้อจำกัด รายงานตรง ๆ |

บรรทัดขึ้นต้นด้วย `!` = มี landmark ซ้ำของวัตถุเดียวกัน → จดไว้ เป็นข้อจำกัด

| อาการ | สาเหตุ | แก้ |
|---|---|---|
| `no landmark of class 'chair'` | กล้องไม่เห็น | ขับเข้าใกล้ เช็กหน้าต่าง yolo |
| ERROR > 1 ม. | ใส่ `--left` ผิดเครื่องหมาย | ขวาต้องเป็นลบ |
| ERROR โตขึ้นทุกด้าน | ตำแหน่งหุ่นบนแผนที่เพี้ยน (ข้อ 1) | จดไว้ วิเคราะห์ในรายงาน |
| `spread` ใหญ่ทั้งที่จอดนิ่ง | หุ่นยังไม่นิ่ง / วัตถุชิดขอบภาพ | รอเพิ่ม 3 วินาที รันใหม่ |

### 2.4 แคปรูประหว่างระบบเปิดครบ (~5 นาที)

| ไฟล์ | วิธี |
|---|---|
| `all_nodes_running.png` | `ros2 node list` → แคปหน้าต่าง terminal |
| `tf_tree.png` | `cd ~ && ros2 run tf2_tools view_frames` → `pdftoppm -png -r 200 -singlefile frames_*.pdf tf_tree` |
| `ros2_node_graph.png` | `rqt_graph` → **Nodes/Topics (active)** → ติ๊ก Hide ทั้งหมด → 🔄 → Save as image |

`tf_tree` ต้องเห็นสาย `map → odom → base_footprint → base_link` ครบ
ไม่มีจอที่ Jetson: `rqt_graph` ต้องใช้ `ssh -X` หรือจอ · `view_frames` กับ `ros2 node list` ใช้ผ่าน SSH ได้

---

## 3. รอบ C — ข้อ 5 CPU (ต่อจากรอบ B ได้เลย)

**ห้ามอัด bag** (zstd กิน CPU) · **ห้ามเปิด RViz / เบราว์เซอร์บน Jetson** · `make yolo` ค่าเริ่มต้น (L engine conf 0.4)

### 3.1 เก็บ

```bash
ros2 run my_bot resource_report.py --seconds 300 --label "full stack yolo26l, driving"   # เปิดครบ + ขับตลอด
ros2 run my_bot resource_report.py --summary
```

ช่วง `idle` / `real+slam` ถ้ายังไม่มี เก็บตอนเปิดระบบรอบไหนก็ได้:
```bash
ros2 run my_bot resource_report.py --seconds 120 --label "idle"         # ก่อนเปิดอะไร
ros2 run my_bot resource_report.py --seconds 180 --label "real+slam"    # ยังไม่เปิด yolo
```

ระหว่างช่วง full stack รันอีก terminal (เผื่อต้องรู้ว่าใครกิน CPU): `top -b -n 1 -o %CPU | head -20`
(`%CPU` ของ `top` คิดต่อ 1 แกน — 100% = เต็ม 1 แกน)

### 3.2 อ่านผล

| บรรทัด | ความหมาย |
|---|---|
| `CPU mean (all 6 cores)` | **ตัวเลขหลัก** เทียบ 80% |
| core ที่สูงสุด | ถ้า > 90% แม้ค่าเฉลี่ยผ่าน → เขียนเรื่องคอขวดแกนเดียวด้วย |
| GPU / RAM / tj | ใส่ย่อหน้าผล · tj ต้องไม่ใกล้ 97 °C |

คาดการณ์: yolo26l engine กิน CPU น้อยกว่า yolo26s ONNX ตัวเก่า (67% vs 72% ของ 1 แกน, `records/objective-tests.md`)
แต่ผลเก่าทั้งระบบคือ 76–81% — **ใกล้เส้นมาก** ต้องวัดจริง

### 3.3 ถ้าเกิน 80%

1. เช็กว่าไม่ได้อัด bag / เปิด RViz / เบราว์เซอร์บน Jetson อยู่
2. ดู `top` ว่าใครกิน แล้วแก้ตรงจุด:

| ตัวที่กินหนัก | แก้ |
|---|---|
| `python3` ของ yolo_detector | เช็กว่า launch ตั้ง `OPENBLAS_NUM_THREADS=1` อยู่ (ตั้งแล้วใน `yolo.launch.py`) |
| `slam_toolbox` | ปรับ `throttle_scans` / `minimum_travel_distance` |
| `cam2image` / `image_republish` | ปกติ — จดไว้ |

3. ปรับอะไรต้องเขียนในรายงาน · **ห้ามเลือกเฉพาะช่วงที่สวย**
4. แก้ไม่ได้ → รายงานไม่ผ่าน พร้อมตารางแยกชั้นว่าใครกินเท่าไหร่

---

## 4. รอบ D — ข้อ 1 ความคลาดเคลื่อนตำแหน่งหุ่น

**เปิด:** `real` → `slam` → `teleop` · ไม่ต้อง yolo / semantic · **ต้องปิด slam ของรอบ B/C ก่อน** แล้วเปิดใหม่ตอนหุ่นจอดที่ HOME

ผลเก่า (`--summary` 24 ก.ย.): ABSOLUTE 104.5 · ALIGNED 42.4 · REPEATABLE 90.2 ซม. — ไฟล์ปน 27 ครั้งจากหลาย session จึงต้องเริ่มใหม่

### 4.1 หลักการ

- `make slam` ตั้งตำแหน่งหุ่นตอนเริ่มเป็น (0,0) · x = ทางหน้าหุ่น · y = ทางซ้าย
- ติดกากบาทจุดอ้างอิงที่พื้น วัดด้วยตลับเมตรว่าอยู่ห่าง HOME เท่าไหร่ = **truth**
- จอดทับกากบาท → สคริปต์อ่านตำแหน่งที่ SLAM บอก เฉลี่ย 5 วินาที
- error = ระยะห่างระหว่างสองตำแหน่งนี้ · แต่ละจุดเทียบกับ truth ของตัวเอง **ไม่บวกต่อกัน**
- ถ้า error ไต่ขึ้นทุกรอบ = ขับเร็วไป / ล้อลื่น

### 4.2 เตรียมพื้นที่ (ก่อนเปิด slam)

1. ย้ายไฟล์ผลเก่าออก (**อย่าลบ**):
   ```bash
   mv ~/maps/slam_accuracy.jsonl ~/maps/slam_accuracy_old.jsonl
   ```
2. ติดกากบาท **HOME** · ขึงเชือก 3–4 ม. เป็นแนวแกน x
3. จอดหุ่นทับ HOME **กึ่งกลางหุ่นทาบแนวเชือก**
4. ติดกากบาทจุดอื่น 3–4 จุด **กระจายทั่วพื้นที่ 5×5 ม.**
5. วัด truth ของ**ทุกจุดจาก HOME / เส้นเชือกโดยตรง** — ห้ามวัดต่อกัน A→B
   x = ตามแนวเชือก · y = ตั้งฉาก ซ้ายบวก ขวาลบ
6. แล้วค่อย `make real` → `make slam` → `make teleop SPEED=0.10`

### 4.3 วัด

```bash
ros2 run my_bot slam_accuracy_check.py mark HOME --truth 0 0     # ต้องได้ ~0 = TF ปกติ
ros2 run my_bot slam_accuracy_check.py mark A --truth <x> <y>
ros2 run my_bot slam_accuracy_check.py mark B --truth <x> <y>
ros2 run my_bot slam_accuracy_check.py mark C --truth <x> <y>
ros2 run my_bot slam_accuracy_check.py mark HOME --truth 0 0     # ปิดรอบ
ros2 run my_bot slam_accuracy_check.py --summary
```

- วนแบบนี้ **อย่างน้อย 3 รอบ** · ขับ 0.10 m/s · จอด**นิ่งสนิท**ก่อนรัน (ขยับเกิน 3 ซม. สคริปต์ไม่รับ)
- **ห้ามปิด/รีสตาร์ท `make slam` กลางคัน** — ถ้าต้องรีสตาร์ท เริ่มใหม่ทั้งชุดและย้ายไฟล์ผลออกก่อน

### 4.4 อ่านผล — รายงานทั้ง 3 ค่า

| ค่า | คืออะไร |
|---|---|
| **ABSOLUTE** | error แย่สุด เทียบ 10 ซม. — ตัวเลขหลัก |
| **ALIGNED** | หลังหักมุมเอียงระหว่างเชือกกับแกนแผนที่ (แบบ ATE) — รายงาน**คู่กับ ABSOLUTE เสมอ** |
| **REPEATABLE** | จอดจุดเดิมหลายรอบ ต่างกันมากสุดเท่าไหร่ — ไม่มีตลับเมตรปน |

`scale` ไม่ใช่ ~1.00 = รัศมีล้อ / ticks เพี้ยน → ข้อสังเกต · ไม่ผ่านทั้งสองค่า → รายงานไม่ผ่าน พร้อมตัวเลขและสาเหตุ

**ห้าม:** ตัดรอบที่แย่ทิ้ง · แก้วัตถุประสงค์หลังเห็นผล · เขียนเงื่อนไขให้ครบ (ความเร็ว ขนาดพื้นที่ จำนวนจุด จำนวนรอบ)
เขียนด้วยว่า error นี้มีการจอดด้วยมือและตลับเมตรปนอยู่ จึงเป็น**ค่าสูงสุด** error จริงของ SLAM เท่ากับหรือดีกว่านี้

---

## 5. รอบ E — รูป Nav2

**เปิด:** `real` → `nav` → `rviz` · **ห้ามเปิด slam พร้อมกัน** · ต้องมีจอหรือ `ssh -X` สำหรับ RViz

```bash
make nav
make rviz
```

กด **2D Goal Pose** → ลากไปจุดที่เส้นทางต้องเลี้ยว → แคปทันทีตอนเส้นสีเขียวขึ้นและเห็นขอบฟ้า/ม่วงรอบสิ่งกีดขวาง
→ `nav2_costmap_path.png`

---

## 6. งานที่โต๊ะ

### 6.1 วาดกราฟ

```bash
cd ~/cap_ws/src/my_bot/scripts
python3 plot_objectives.py slam                              # หลังรอบ D
python3 plot_objectives.py resource --window "full stack"    # หลังรอบ C
```
ได้ `slam_error_result.png` กับ `resource_usage.png` ที่ `~/cap_ref/figures/`

ข้อ 4: `plot_objectives.py object` อ่านไฟล์ของสคริปต์ตัวเก่า ใช้กับผลใหม่ไม่ได้ → รายงานเป็น**ตาราง 4 แถว**จาก `object_accuracy.py --summary`

### 6.2 เอาผลไปใส่ในรายงาน (`project_report-good3.tex`)

| ได้ตัวเลขจาก | ใส่ที่ |
|---|---|
| `slam_accuracy_check.py --summary` | `tab:eval` แถว 1 + รูป `slam_error_result.png` |
| `object_accuracy.py --summary` | `tab:eval` แถว 4 + ตาราง 4 ด้าน |
| `resource_report.py --summary` | `tab:eval` แถว 5 + รูป `resource_usage.png` + ตารางแยกชั้น |
| ~~ข้อ 2~~ ~~ข้อ 3~~ | ✅ ใส่แล้ว (`sec:eval-det`, `tab:eval` แถว 2–3) |

**ส่งมาให้ Claude:** ผล `--summary` ทั้ง 3 ตัว + รูป → เติมรายงานและแก้ข้อความที่ขัดกัน

### 6.3 รูปที่ต้องก๊อปไป `CapstoneReport/images/`

| รูป | สถานะ |
|---|---|
| `accuracy_before_after.png` · `detection_fps.png` | ✅ มีแล้วที่ `~/cap_ref/figures/` — ก๊อปได้เลย |
| `tf_tree.png` · `ros2_node_graph.png` | ✅ มีแล้วที่ `~/cap_ref/figures/` (`node_graph.py` ไม่ต้องมีจอ) |
| `all_nodes_running.png` | ✅ ใส่แล้ว |
| `resource_usage.png` | ✅ มีแล้ว |
| `slam_error_result.png` | รอบ D → 6.1 |
| `nav2_costmap_path.png` | ✅ ใส่แล้ว (local costmap เท่านั้น ไม่มีเส้นทาง/เป้าหมาย) |

### 6.4 เช็กลิสต์ก่อนส่ง

- [x] `tab:eval` แถว 2 และ 3
- [ ] `tab:eval` แถว 1, 4, 5 — ข้อไหนไม่ผ่าน เขียนค่าจริงพร้อมเหตุผล **อย่าเว้นว่าง**
- [ ] ลบข้อความ "ยังไม่ได้วัด" ที่เหลือ (บทคัดย่อเรื่อง SLAM · สรุปผล · ย่อหน้าเหตุผลใต้ `tab:eval` · ข้อเสนอแนะข้อ 1)
- [ ] แทน `\imgph` ครบ 6 จุด (`ros2_node_graph` `tf_tree` `nav2_costmap_path` `slam_error_result` `resource_usage` `all_nodes_running`)
- [ ] ก๊อปไฟล์ jsonl ทุกตัวจาก `~/maps/` เก็บเป็นหลักฐาน
- [ ] คอมไพล์บนเครื่องที่มี LaTeX (Jetson ไม่มี) ตรวจ `.log` ว่าไม่มี error และ undefined reference
      — ใหม่ในรอบนี้: `\ref{sec:eval-det}` · ตาราง `tab:det-*` · `\subsubsection` · รูป `accuracy_before_after.png` `detection_fps.png`

---

## ภาคผนวก — ข้อ 2 ทำอะไรไปแล้ว (อ้างอิง)

- ชุดภาพ: bag `2026-09-24-165025` · 143 ภาพ (`--matched-only --every 23`) · `~/eval/insitu2_stationary`
- label: yolo26x ร่าง → ตรวจแก้ในเบราว์เซอร์ (`label_server.py`) ทุกภาพ · สำรองที่ `records/objective2-data/`
- เงื่อนไข / ข้อจำกัด: D-27 (มุมมองเดียว) · D-29 (ปรับบนชุดเดียวกัน ไม่มีชุดทดสอบแยก)
- ตารางพัฒนาการ s → m → L, TensorRT, ขนาดภาพ, ทรัพยากร: `records/objective-tests.md` → Objective 2 → Run log
- engine: `~/yolo/yolo26l_480x640.engine` = ค่าเริ่มต้นของ `make yolo` (D-30) · build ใหม่ด้วย `make yolo-engine FORCE=true` (~13 นาที ห้ามตอนเปิดทั้งระบบ)
