import logging


def mix_stems(processed_audio_dict, output_path, source_duration_ms=None):
    """
    Overlays all processed stems into a single output track.
    If source_duration_ms is provided, validates the output duration matches (plan requirement).
    """
    final_mix = None
    for stem_audio in processed_audio_dict.values():
        if final_mix is None:
            final_mix = stem_audio
        else:
            final_mix = final_mix.overlay(stem_audio)

    final_mix = final_mix + 3

    # --- Plan: Stage C Validation: Output Duration == Input Duration ---
    if source_duration_ms is not None:
        out_ms = len(final_mix)
        tolerance_ms = 500  # allow 500ms tolerance for codec rounding
        if abs(out_ms - source_duration_ms) > tolerance_ms:
            raise RuntimeError(
                f"Duration mismatch after mixing: "
                f"input={source_duration_ms}ms, output={out_ms}ms "
                f"(delta={abs(out_ms - source_duration_ms)}ms > {tolerance_ms}ms tolerance)"
            )
        logging.info(f"Duration validation passed: {out_ms}ms ≈ {source_duration_ms}ms")

    final_mix.export(output_path, format="mp3", bitrate="64k")
    return output_path
