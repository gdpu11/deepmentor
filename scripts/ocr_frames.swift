// Read original-publisher frame subtitles for transcript cross-checking.
// Input: one absolute image path per line. Output: append-only JSONL; no evidence approval.
import Foundation
import Vision
import ImageIO

if CommandLine.arguments.count != 3 {
    fputs("usage: ocr-frames frame-paths.txt output.jsonl\n", stderr)
    exit(2)
}
let list = try String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)
let output = CommandLine.arguments[2]
if !FileManager.default.fileExists(atPath: output) {
    FileManager.default.createFile(atPath: output, contents: nil)
}
let handle = try FileHandle(forWritingTo: URL(fileURLWithPath: output))
try handle.seekToEnd()
var done = Set<String>()
if let existing = try? String(contentsOfFile: output, encoding: .utf8) {
    for line in existing.split(separator: "\n") {
        if let data = line.data(using: .utf8), let row = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           row["error"] == nil, let path = row["file"] as? String { done.insert(path) }
    }
}
for line in list.split(separator: "\n") {
    let path = String(line)
    if done.contains(path) { continue }
    autoreleasepool {
        var row: [String: Any] = ["file": path, "verification": "pending"]
        do {
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.recognitionLanguages = ["zh-Hans", "en-US"]
            request.usesLanguageCorrection = false
            // Vision coordinates start at the lower left. Original frame is retained separately.
            request.regionOfInterest = CGRect(x: 0, y: 0, width: 1, height: 0.29)
            try VNImageRequestHandler(url: URL(fileURLWithPath: path)).perform([request])
            row["lines"] = (request.results ?? []).compactMap { observation -> [String: Any]? in
                guard let text = observation.topCandidates(1).first else { return nil }
                let b = observation.boundingBox
                return ["text": text.string, "confidence": text.confidence,
                        "box": [b.origin.x, b.origin.y, b.size.width, b.size.height]]
            }
        } catch { row["error"] = String(describing: error) }
        if let data = try? JSONSerialization.data(withJSONObject: row, options: [.sortedKeys]) {
            try? handle.write(contentsOf: data)
            try? handle.write(contentsOf: Data([10]))
        }
    }
}
try handle.close()
