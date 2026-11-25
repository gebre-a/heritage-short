# CELL 1
!nvidia-smi
!git clone https://github.com/ACE-Step/ACE-Step-1.5.git
%cd ACE-Step-1.5
# Install and download weights EXACTLY as the repo README says today.

# CELL 2: use the README's generation example with these inputs, for seeds 7, 8, 9:
#   caption  = "warm, gentle, sparse acoustic guitar and soft strings, pentatonic feel, calm, instrumental, no strong lead melody"
#   duration = 60..80 seconds (30-60 s is most stable; generate two parts and join if needed)
#   bpm=72, key="D minor"  (these go in the metadata fields, NOT the caption)
#   instrumental / no lyrics
# Save outputs as cand_1.wav, cand_2.wav, cand_3.wav, download them to outputs/music/