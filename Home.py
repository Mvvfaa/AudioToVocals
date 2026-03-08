import streamlit as st

st.set_page_config(page_title="AudioSep", layout="wide")

st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@500&display=swap');

	.stApp {
		background:
			radial-gradient(circle at 20% 10%, rgba(255, 184, 77, 0.28), transparent 35%),
			radial-gradient(circle at 85% 20%, rgba(0, 184, 148, 0.23), transparent 40%),
			linear-gradient(140deg, #0f1720 0%, #142035 45%, #1b2f24 100%);
	}

	.hero {
		padding: 2.2rem;
		border-radius: 20px;
		border: 1px solid rgba(255, 255, 255, 0.16);
		background: linear-gradient(140deg, rgba(8, 14, 25, 0.78), rgba(16, 28, 36, 0.72));
		box-shadow: 0 16px 38px rgba(0, 0, 0, 0.36);
		animation: fadeSlide 0.75s ease-out;
	}

	.brand {
		font-family: 'Space Grotesk', sans-serif;
		font-size: 3rem;
		font-weight: 700;
		line-height: 1.05;
		color: #f6f8fb;
		margin-bottom: 0.45rem;
	}

	.subtitle {
		font-family: 'Space Grotesk', sans-serif;
		font-size: 1.06rem;
		color: #d8e4e8;
		max-width: 760px;
		margin-bottom: 1rem;
	}

	.chip {
		display: inline-block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.78rem;
		letter-spacing: 0.02em;
		color: #ffe4c7;
		border: 1px solid rgba(255, 226, 191, 0.42);
		background: rgba(255, 184, 77, 0.16);
		border-radius: 999px;
		padding: 0.3rem 0.75rem;
	}

	.section-title {
		font-family: 'Space Grotesk', sans-serif;
		font-size: 1.15rem;
		font-weight: 600;
		color: #f7f9fb;
		margin: 1.4rem 0 0.8rem 0;
	}

	.card {
		padding: 1.15rem;
		border-radius: 16px;
		min-height: 168px;
		border: 1px solid rgba(255, 255, 255, 0.15);
		background: linear-gradient(160deg, rgba(10, 18, 28, 0.76), rgba(21, 31, 46, 0.68));
		box-shadow: 0 10px 26px rgba(0, 0, 0, 0.25);
		transition: transform 0.22s ease, box-shadow 0.22s ease;
	}

	.card:hover {
		transform: translateY(-4px);
		box-shadow: 0 16px 36px rgba(0, 0, 0, 0.34);
	}

	.card h3 {
		font-family: 'Space Grotesk', sans-serif;
		font-weight: 700;
		color: #f4f7fb;
		margin: 0 0 0.3rem 0;
	}

	.card p {
		font-family: 'Space Grotesk', sans-serif;
		color: #d1dde3;
		margin: 0;
		line-height: 1.5;
	}

	@keyframes fadeSlide {
		from {
			opacity: 0;
			transform: translateY(14px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (max-width: 740px) {
		.brand {
			font-size: 2.3rem;
		}

		.hero {
			padding: 1.3rem;
		}
	}
	</style>
	""",
	unsafe_allow_html=True,
)

st.markdown(
	"""
	<div class="hero">
		<div class="chip">AudioSep Suite</div>
		<div class="brand">Split songs with MDX and Demucs</div>
		<div class="subtitle">
			Choose your separation engine from the pages below.
			Use <b>MDX</b> for the two-step UVR-style pipeline, or <b>Demucs</b>
			for high-quality stem separation in one run.
		</div>
	</div>
	""",
	unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Choose Your Workflow</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
	st.markdown(
		"""
		<div class="card">
			<h3>MDX Pipeline</h3>
			<p>Two-step extraction and cleaning, ideal when you want extra control over vocal refinement.</p>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.page_link("pages/1_MDX.py", label="Open MDX Page", icon="🎤")

# with col2:
# 	st.markdown(
# 		"""
# 		<div class="card">
# 			<h3>Demucs Pipeline</h3>
# 			<p>Model-based stem separation with vocals isolation, fast setup, and consistent quality.</p>
# 		</div>
# 		""",
# 		unsafe_allow_html=True,
# 	)
# 	st.page_link("pages/2_Demucs.py", label="Open Demucs Page", icon="🎧")

with col2:
	st.markdown(
		"""
		<div class="card">
			<h3>Demucs Pipeline</h3>
			<p>Model-based stem separation with vocals isolation, fast setup, and consistent quality.</p>
			<p style="margin-top:0.75rem;"><span class="chip">Coming Soon</span></p>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.caption("Demucs workflow is in progress and will be available in a future update.")