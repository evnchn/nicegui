export default {
  template: `
    <div style="display: inline-flex; align-items: center; gap: 8px;">
      <button
        @click="toggle"
        :style="buttonStyle"
        :title="recording ? 'Stop recording' : 'Start recording'"
      >
        <span v-if="recording" style="display:inline-block;width:14px;height:14px;background:currentColor;border-radius:2px;"></span>
        <span v-else style="display:inline-block;width:14px;height:14px;background:#e53935;border-radius:50%;"></span>
      </button>
      <span v-if="recording" style="color: #e53935; font-size: 0.85em;">● Recording</span>
    </div>
  `,
  props: {
    url: String,
    mimeType: String,
  },
  data() {
    return {
      recording: false,
      mediaRecorder: null,
      audioChunks: [],
      computed_url: undefined,
    };
  },
  computed: {
    buttonStyle() {
      return {
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: "36px",
        height: "36px",
        borderRadius: "50%",
        border: "2px solid " + (this.recording ? "#e53935" : "#888"),
        background: "transparent",
        cursor: "pointer",
        padding: "0",
        color: this.recording ? "#e53935" : "#888",
      };
    },
  },
  mounted() {
    setTimeout(() => this.compute_url(), 0);
  },
  updated() {
    this.compute_url();
  },
  methods: {
    compute_url() {
      this.computed_url = (this.url.startsWith("/") ? window.path_prefix : "") + this.url;
    },
    toggle() {
      if (this.recording) {
        this.stop();
      } else {
        this.start();
      }
    },
    async start() {
      if (this.recording) return;
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const options = {};
        if (this.mimeType && MediaRecorder.isTypeSupported(this.mimeType)) {
          options.mimeType = this.mimeType;
        }
        this.mediaRecorder = new MediaRecorder(stream, options);
        this.audioChunks = [];
        this.mediaRecorder.addEventListener("dataavailable", (event) => {
          if (event.data.size > 0) {
            this.audioChunks.push(event.data);
          }
        });
        this.mediaRecorder.addEventListener("stop", () => {
          stream.getTracks().forEach((track) => track.stop());
          const mimeType = this.mediaRecorder.mimeType || "audio/webm";
          const audioBlob = new Blob(this.audioChunks, { type: mimeType });
          this.uploadAudio(audioBlob, mimeType);
        });
        this.mediaRecorder.start();
        this.recording = true;
        this.$emit("start");
      } catch (err) {
        console.error("Failed to start audio recording:", err);
      }
    },
    stop() {
      if (!this.recording || !this.mediaRecorder) return;
      this.mediaRecorder.stop();
      this.recording = false;
      this.$emit("stop");
    },
    async uploadAudio(blob, mimeType) {
      const ext = mimeType.split(";")[0].split("/")[1] || "webm";
      const filename = "recording." + ext;
      const formData = new FormData();
      formData.append("file", blob, filename);
      try {
        await fetch(this.computed_url, {
          method: "POST",
          body: formData,
        });
      } catch (err) {
        console.error("Failed to upload audio recording:", err);
      }
    },
  },
};
