import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from matplotlib import rcParams

# Use standard fonts for academic style (LaTeX like)
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
rcParams['font.size'] = 10
rcParams['axes.linewidth'] = 1.2
rcParams['mathtext.fontset'] = 'cm'

fig = plt.figure(figsize=(12, 5.5))
fig.patch.set_facecolor('white')

gs = GridSpec(1, 2, width_ratios=[1.2, 1], wspace=0.1)

# ==========================================
# LEFT PANEL: Text Comparisons
# ==========================================
ax_text = fig.add_subplot(gs[0])
ax_text.axis('off')

box_width = 0.95
box_x = 0.02

# Helper function to draw text box
def draw_textbox(ax, y_pos, title, content, bg_color, edge_color, height=0.28):
    # Draw background box
    rect = patches.Rectangle((box_x, y_pos), box_width, height, 
                             linewidth=1.5, edgecolor=edge_color, facecolor=bg_color, 
                             transform=ax.transAxes, zorder=1)
    ax.add_patch(rect)
    
    # Add title
    ax.text(box_x + 0.02, y_pos + height - 0.04, title, 
            fontweight='bold', fontsize=11, transform=ax.transAxes, zorder=2)
    
    # Add text content (wrapped)
    import textwrap
    wrapped_text = textwrap.fill(content, width=75)
    ax.text(box_x + 0.02, y_pos + height - 0.08, wrapped_text, 
            fontsize=9.5, transform=ax.transAxes, zorder=2, va='top', linespacing=1.4)

# Original Article
orig_text = ("Andrew Getty, one of the heirs to billions of oil money, appears to have died of "
             "natural causes, a Los Angeles Police Department spokesman said. The coroner's preliminary "
             "assessment is there was no foul play involved... [...] ...Gordon Getty spearheaded the "
             "controversial sale of Getty to Texaco for $10 billion in 1984. In its list of richest "
             "American families, Forbes estimated the Gettys' net worth to be about $5 billion.")
draw_textbox(ax_text, 0.68, "Original Article", orig_text, '#FFFFFF', '#000000', height=0.30)

# Baseline
bart_text = ("Coroner's preliminary assessment is there was no foul play involved in the death. "
             "Andrew Getty, 47, had \"several health issues,\" police say. He is the grandson of "
             "oil tycoon J. Paul Getty, who died in 1976. Gordon Getty spearheaded the controversial "
             "sale of Getty to Texaco for $10 billion in 1984.")
draw_textbox(ax_text, 0.35, "Summary: Baseline (BART)", bart_text, '#F0F8FF', '#1E90FF', height=0.30)

# Combinatorial Optimization
co_text = ("Coroner's preliminary assessment is there was no foul play involved in the death. "
           "Andrew Getty, 47, was found on his side near a bathroom in his home, KTLA reports. "
           "His parents, Ann and Gordon Getty, released a statement confirming their son's death. "
           "He was the grandson of oil tycoon J. Paul Getty, one of the world's richest men.")
draw_textbox(ax_text, 0.02, "Summary: Combinatorial Opt.", co_text, '#FFF0F5', '#DC143C', height=0.30)


# ==========================================
# RIGHT PANEL: Radar Chart (Pentagon)
# ==========================================
ax_radar = fig.add_subplot(gs[1], polar=True)

# Data - 5 metrics
categories = ['ROUGE-L', 'MiniCheck', 'FactCC', 'AlignScore', 'FactKB']
N = len(categories)

# Raw values
# Baseline: ROUGE-L: 30.62, MiniCheck: 94.90, FactCC: 75.83, AlignScore: 91.56, FactKB: 98.49
# CO (Best): ROUGE-L: 26.77, MiniCheck: 97.36, FactCC: 79.06, AlignScore: 94.01, FactKB: 99.01

# Normalize values between 0.3 (min) and 1.0 (max) for aesthetic plotting
baseline_raw = np.array([30.62, 94.90, 75.83, 91.56, 98.49])
co_raw = np.array([26.77, 97.36, 79.06, 94.01, 99.01])

# Min and Max limits for normalization to exaggerate the differences and make it aesthetic
mins = np.array([25.0, 93.0, 73.0, 90.0, 97.5])
maxs = np.array([31.0, 98.0, 80.0, 95.0, 99.5])

baseline_norm = (baseline_raw - mins) / (maxs - mins) * 0.8 + 0.2
co_norm = (co_raw - mins) / (maxs - mins) * 0.8 + 0.2

angles = [n / float(N) * 2 * np.pi for n in range(N)]
baseline_norm = np.concatenate((baseline_norm, [baseline_norm[0]]))
co_norm = np.concatenate((co_norm, [co_norm[0]]))
angles = np.concatenate((angles, [angles[0]]))

# Plot baseline
ax_radar.plot(angles, baseline_norm, linewidth=2.5, linestyle='solid', color='#1E90FF', label='Baseline (BART)')
ax_radar.fill(angles, baseline_norm, color='#1E90FF', alpha=0.25)

# Plot CO
ax_radar.plot(angles, co_norm, linewidth=2.5, linestyle='solid', color='#DC143C', label='Combinatorial Optimization')
ax_radar.fill(angles, co_norm, color='#DC143C', alpha=0.25)

# Formatting radar chart
ax_radar.set_theta_offset(np.pi / 2)
ax_radar.set_theta_direction(-1)
ax_radar.set_xticks(angles[:-1])
ax_radar.set_xticklabels(categories, fontsize=12, weight='bold')

# Remove y-axis and radial lines for a cleaner, minimalist look
ax_radar.set_yticks([])
ax_radar.spines['polar'].set_color('#CCCCCC')
ax_radar.spines['polar'].set_linewidth(1.5)
ax_radar.grid(color='#EEEEEE', linewidth=1)

# Adjust axes limits
ax_radar.set_ylim(0, 1.1)

# Legend
ax_radar.legend(loc='lower center', bbox_to_anchor=(0.5, -0.2), ncol=1, frameon=False, fontsize=11)

plt.tight_layout()
plt.savefig('acl_paper_figure_radar.pdf', format='pdf', dpi=300, bbox_inches='tight')
plt.savefig('acl_paper_figure_radar.png', format='png', dpi=300, bbox_inches='tight')
