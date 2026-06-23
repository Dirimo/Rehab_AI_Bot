<script setup lang="ts">
import type { Group, PerspectiveCamera, Scene, WebGLRenderer } from 'three'
import type { GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js'

const props = withDefaults(
  defineProps<{
    size?: number
    rotate?: boolean
  }>(),
  { size: 56, rotate: true },
)

const mountEl = ref<HTMLElement | null>(null)
const failed = ref(false)

let frameId = 0
let disposed = false
let renderer: WebGLRenderer | null = null
let scene: Scene | null = null
let camera: PerspectiveCamera | null = null
let model: Group | null = null

function cleanup() {
  disposed = true
  cancelAnimationFrame(frameId)
  renderer?.dispose()
  if (renderer?.domElement && mountEl.value?.contains(renderer.domElement)) {
    mountEl.value.removeChild(renderer.domElement)
  }
  renderer = null
  scene = null
  camera = null
  model = null
}

function startRenderLoop() {
  const tick = () => {
    if (disposed || !renderer || !scene || !camera) return
    frameId = requestAnimationFrame(tick)
    if (model && props.rotate) model.rotation.y += 0.01
    renderer.render(scene, camera)
  }
  tick()
}

async function initViewer(el: HTMLElement) {
  disposed = false
  failed.value = false

  try {
    const THREE = await import('three')
    const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader.js')

    const width = props.size
    const height = props.size

    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(35, width / height, 0.01, 100)
    camera.position.set(0, 0, 2.8)

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    el.appendChild(renderer.domElement)

    scene.add(new THREE.HemisphereLight(0xffffff, 0x8ab4d9, 1.35))
    scene.add(new THREE.AmbientLight(0xffffff, 0.55))
    const key = new THREE.DirectionalLight(0xffffff, 1.25)
    key.position.set(2, 4, 5)
    scene.add(key)
    const fill = new THREE.DirectionalLight(0xbbd9f5, 0.65)
    fill.position.set(-3, 1, 2)
    scene.add(fill)

    startRenderLoop()

    const loader = new GLTFLoader()
    loader.load(
      '/rehabbot-logo.glb',
      (gltf: GLTF) => {
        if (disposed || !scene) return

        model = gltf.scene
        const box = new THREE.Box3().setFromObject(model)
        const center = box.getCenter(new THREE.Vector3())
        const dimensions = box.getSize(new THREE.Vector3())
        const maxDim = Math.max(dimensions.x, dimensions.y, dimensions.z) || 1
        const scale = 2.2 / maxDim

        model.position.sub(center)
        model.scale.setScalar(scale)

        const fitted = new THREE.Box3().setFromObject(model)
        const sphere = fitted.getBoundingSphere(new THREE.Sphere())
        camera.position.z = Math.max(sphere.radius * 2.4, 2.5)
        camera.lookAt(0, 0, 0)
        scene.add(model)
      },
      undefined,
      (error: unknown) => {
        console.error('Failed to load RehabBot logo:', error)
        failed.value = true
      },
    )
  } catch (error) {
    console.error('Failed to init RehabBot logo viewer:', error)
    failed.value = true
  }
}

onMounted(async () => {
  await nextTick()
  if (!mountEl.value) return
  await initViewer(mountEl.value)
})

onBeforeUnmount(cleanup)
</script>

<template>
  <div
    class="brand-logo-3d"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="img"
    aria-label="Logo RehabBot"
  >
    <div ref="mountEl" class="brand-logo-3d__canvas" />
    <svg
      v-if="failed"
      class="brand-logo-3d__fallback"
      :width="size"
      :height="size"
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="32" cy="32" r="28" stroke="#BBD9F5" stroke-width="2" stroke-dasharray="6 4" />
      <rect x="14" y="18" width="36" height="28" rx="10" fill="#BBD9F5" />
      <path d="M22 46 L28 52 L28 46 Z" fill="#BBD9F5" />
      <circle cx="26" cy="32" r="2.5" fill="#0A0A0A" />
      <circle cx="38" cy="32" r="2.5" fill="#0A0A0A" />
    </svg>
  </div>
</template>

<style scoped>
.brand-logo-3d {
  display: block;
  flex-shrink: 0;
  line-height: 0;
  position: relative;
}

.brand-logo-3d__canvas {
  width: 100%;
  height: 100%;
}

.brand-logo-3d__canvas :deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

.brand-logo-3d__fallback {
  display: block;
}
</style>
