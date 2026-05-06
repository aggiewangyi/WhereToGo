/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AGENT_API_KEY?: string
}
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
