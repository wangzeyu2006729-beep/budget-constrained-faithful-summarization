import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import argparse

def create_radar_and_stitch(input_path, output_path):
    print(f"Loading '{input_path}'...")
    
    # 1. Data Values (Visual Scale 0.0 - 1.0 configured to strictly mirror user requirements)
    categories = ['ROUGE-L', 'MiniCheck', 'FactCC', 'AlignScore', 'FactKB']
    N = len(categories)

    # 红色在ROUGE上被适度降低 (不再极高), 蓝色在四维被适度提升 (间距缩小), 同时保持红色在四维超越蓝色
    blue_norm = np.array([0.90, 0.50, 0.45, 0.50, 0.55])
    red_norm  = np.array([0.80, 0.95, 0.90, 0.95, 1.00])

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    blue_norm = np.concatenate((blue_norm, [blue_norm[0]]))
    red_norm = np.concatenate((red_norm, [red_norm[0]]))
    angles = np.concatenate((angles, [angles[0]]))

    # 2. Draw precise radar using Matplotlib (academic standard)
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
    plt.rcParams['font.size'] = 14

    fig, ax = plt.subplots(figsize=(6.5, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    ax.plot(angles, blue_norm, linewidth=2.5, linestyle='solid', color='#4F81BD')
    ax.fill(angles, blue_norm, color='#4F81BD', alpha=0.55)

    ax.plot(angles, red_norm, linewidth=2.5, linestyle='solid', color='#C0504D')
    ax.fill(angles, red_norm, color='#C0504D', alpha=0.45)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=15, weight='bold')

    # Remove standard circular grid/spines
    ax.set_yticks([])
    ax.spines['polar'].set_visible(False)
    ax.grid(False)

    # Draw academic pentagonal grid limits manually
    for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
        grid_points = np.concatenate(([r]*N, [r]))
        ax.plot(angles, grid_points, color='#333333', linewidth=1.2 if r==1.0 else 0.5, zorder=0)

    ax.set_ylim(0, 1.08)

    # Precise Legend Matching the Image
    import matplotlib.patches as patches
    blue_patch = patches.Rectangle((0,0), 1, 1, facecolor='#4F81BD', edgecolor='black')
    red_patch = patches.Rectangle((0,0), 1, 1, facecolor='#C0504D', edgecolor='black')
    ax.legend([blue_patch, red_patch], ['Baseline\n(BART)', 'Combinatorial\nOptimization'], 
              loc='lower center', bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, 
              fontsize=14, handlelength=1.5, handleheight=0.6, labelspacing=1.5)

    plt.tight_layout()
    plt.savefig('temp_radar.png', format='png', dpi=400, bbox_inches='tight')
    plt.close()

    # 3. Stitch Left (original text) with Right (new radar) transparently
    print("Stitching left column logic with new radar chart...")
    orig_img = Image.open(input_path).convert('RGB')
    W, H = orig_img.size
    radar_img = Image.open('temp_radar.png').convert('RGB')
    
    # Assuming text boxes do not cross the 45% width line
    left_w = int(W * 0.45)
    radar_w = W - left_w
    
    r_w, r_h = radar_img.size
    scale = min((radar_w * 0.95) / r_w, (H * 0.86) / r_h)
    new_w, new_h = int(r_w * scale), int(r_h * scale)
    radar_img = radar_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    final_img = Image.new('RGB', (W, H), (255, 255, 255))
    final_img.paste(orig_img.crop((0, 0, left_w, H)), (0, 0))
    
    offset_x = left_w + (radar_w - new_w) // 2
    offset_y = (H - new_h) // 2
    final_img.paste(radar_img, (offset_x, offset_y))
    
    final_img.save(output_path)
    os.remove('temp_radar.png')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='/home/zeyu/projects/NLM_ilp_dpp_mmr_experiment/bart/results/source_figure.png')
    parser.add_argument('--output', type=str, default='/home/zeyu/projects/NLM_ilp_dpp_mmr_experiment/bart/results/acl_figure_revised.png')
    args = parser.parse_args()
    
    if os.path.exists(args.input):
        create_radar_and_stitch(args.input, args.output)
        print(f"✅ Success! Revised image seamlessly saved to: {args.output}")
    else:
        print(f"❌ Error: Could not find '{args.input}'. Please upload/save the image to this path first.")
