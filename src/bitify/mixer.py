def mix_stems(processed_audio_dict, output_path):
    final_mix = None
    for stem_audio in processed_audio_dict.values():
        if final_mix is None:
            final_mix = stem_audio
        else:
            final_mix = final_mix.overlay(stem_audio)

    final_mix = final_mix + 3
    final_mix.export(output_path, format="mp3", bitrate="64k")
    return output_path
