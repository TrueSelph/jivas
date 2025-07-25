import{w as h,z as g}from"./chunk-QMGIS6GS-CBZUm-7V.js";import{j as t}from"./jsx-runtime-D_zvdyIk.js";import{B as c}from"./polymorphic-factory-EW0USS3V.js";import{G as f}from"./Group-bnACpcuK.js";import{A as u}from"./ActionIcon-BO4DDcDR.js";import{I as _}from"./IconArrowLeft-4qKQ7vAI.js";import{T as y}from"./Title-B0fFn55O.js";import{D as j}from"./Divider-BI4N1hoX.js";import"./Loader-1VreoqJz.js";import"./index-B4z8r-Ct.js";import"./createReactComponent-CwEnMXT7.js";async function R({request:e}){const r=(await e.formData()).get("agentId");return localStorage.setItem("jivas-agent",r),{}}function v(e){return e.replace(/\\/g,"\\\\").replace(/`/g,"\\`").replace(/\${/g,"\\${")}async function P({serverLoader:e,params:o}){const r=localStorage.getItem("jivas-host"),p=localStorage.getItem("jivas-root-id"),n=localStorage.getItem("jivas-token"),m=localStorage.getItem("jivas-token-exp"),a=localStorage.getItem("jivas-agent"),s=await fetch(`${r}/walker/get_action`,{method:"POST",body:JSON.stringify({agent_id:a,action_id:o.actionId,reporting:!0}),headers:{"Content-Type":"application/json",Authorization:`Bearer ${n}`}}).then(i=>i.json()),d=await fetch(`${r}/walker/get_action_app`,{method:"POST",body:JSON.stringify({agent_id:a,action:s.reports[0].label,reporting:!0}),headers:{"Content-Type":"application/json",Authorization:`Bearer ${n}`}}).then(i=>i.json()).then(i=>{var l;return((l=i.reports)==null?void 0:l[0])||""});return{code:`
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Serverless Image Processing App</title>
    <meta name="description" content="A Serverless Streamlit application with OpenCV image processing that completely works on your browser">
      <link
        rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/@stlite/browser@0.83.0/build/stlite.css"
      />
  </head>
  <body>
    <div id="root"></div>
    <script type="module">
    	import { mount } from "https://cdn.jsdelivr.net/npm/@stlite/browser@0.83.0/build/stlite.js";
      mount({
        requirements: [
                  "PyYAML",
                  "requests",
                  "https://pub-62dafe7bf3a84354ad20209ffaed5137.r2.dev/streamlit_router-0.1.8-py3-none-any.whl",
                  "jvclient",
                  "matplotlib",
                  "opencv-python",
                ],
        entrypoint: "streamlit_app.py",
        files: {
          "streamlit_app.py": \`${{"streamlit_app.py":`
import os
import streamlit as st
import json
from streamlit_router import StreamlitRouter

${v(d.replaceAll("jvcli.client","jvclient").replaceAll("`","'"))}


root_id = "${p||""}"
print("ROOT ID:", root_id)
st.session_state.ROOT_ID = root_id or "000000000000000000000000"
st.session_state.TOKEN = "${n}"
st.session_state.EXPIRATION = ${m||0xe674660f0edc}


if __name__ == "__main__":
    router = StreamlitRouter()
    os.environ["JIVAS_BASE_URL"] = "${r||"http://localhost:8000"}";


    agent_id = "${a}"
    action_id = "${o.actionId}"

    info = json.loads('${JSON.stringify(s.reports[0]._package)}')

    render(router, agent_id, action_id, info)
    `}["streamlit_app.py"]}\`,
        },
      },
      document.getElementById("root"))
    <\/script>
  </body>
  </html>
				`}}const B=h(function({loaderData:o}){return t.jsxs(c,{px:"xl",py:"xl",children:[t.jsxs(f,{children:[t.jsx(u,{color:"dark",size:"sm",component:g,to:"./..",children:t.jsx(_,{})}),t.jsx(y,{order:3,children:"Manage Action"})]}),t.jsx(j,{mt:"xs",mb:"xl"}),t.jsx(c,{px:"xl",py:"xl",h:"90vh",children:t.jsx("iframe",{style:{outline:"none",border:"none"},title:"Action Config",width:"100%",height:"100%",srcDoc:o.code})})]})});export{R as clientAction,P as clientLoader,B as default};
