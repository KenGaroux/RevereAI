use std::fs;
use std::io;
use std::path::Path;

struct Frame {
    name: &'static str,
    x: u32,
    y: u32,
    w: u32,
    h: u32,
}

fn main() -> io::Result<()> {
    let output_path = Path::new("../../python/core/assets/reverie_frames.json");
    let frames = [
        Frame { name: "speak_l", x: 52, y: 82, w: 244, h: 302 },
        Frame { name: "thinking", x: 384, y: 82, w: 244, h: 302 },
        Frame { name: "speak_o", x: 716, y: 82, w: 244, h: 302 },
        Frame { name: "query", x: 52, y: 428, w: 244, h: 302 },
        Frame { name: "idle", x: 384, y: 428, w: 244, h: 302 },
        Frame { name: "active", x: 716, y: 428, w: 244, h: 302 },
        Frame { name: "surprise", x: 52, y: 770, w: 244, h: 302 },
        Frame { name: "speak_m", x: 384, y: 770, w: 244, h: 302 },
        Frame { name: "soft", x: 716, y: 770, w: 244, h: 302 },
    ];

    let mut json = String::from("{\n");
    json.push_str("  \"sheet\": \"/reve-animations/reve%20faces%201.png\",\n");
    json.push_str("  \"sheet_width\": 991,\n");
    json.push_str("  \"sheet_height\": 1088,\n");
    json.push_str("  \"frames\": {\n");

    for (index, frame) in frames.iter().enumerate() {
        let comma = if index + 1 == frames.len() { "" } else { "," };
        json.push_str(&format!(
            "    \"{}\": {{ \"x\": {}, \"y\": {}, \"w\": {}, \"h\": {} }}{}\n",
            frame.name, frame.x, frame.y, frame.w, frame.h, comma
        ));
    }

    json.push_str("  },\n");
    json.push_str("  \"sequences\": {\n");
    json.push_str("    \"idle\": [\"idle\"],\n");
    json.push_str("    \"active\": [\"active\"],\n");
    json.push_str("    \"thinking\": [\"thinking\", \"query\"],\n");
    json.push_str("    \"speaking\": [\"speak_l\", \"speak_m\", \"speak_o\", \"soft\"]\n");
    json.push_str("  }\n");
    json.push_str("}\n");

    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(output_path, json)?;
    println!("wrote {}", output_path.display());
    Ok(())
}
