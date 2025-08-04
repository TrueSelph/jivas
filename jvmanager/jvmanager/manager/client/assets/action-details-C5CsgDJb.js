import{w as j,z as v}from"./chunk-QMGIS6GS-CBZUm-7V.js";import{j as e}from"./jsx-runtime-D_zvdyIk.js";import{f as d}from"./api-tgDzxHzW.js";import{B as h}from"./polymorphic-factory-EW0USS3V.js";import{G as I}from"./Group-bnACpcuK.js";import{A as x}from"./ActionIcon-BO4DDcDR.js";import{I as S}from"./IconArrowLeft-4qKQ7vAI.js";import{T as A}from"./Title-B0fFn55O.js";import{D as w}from"./Divider-BI4N1hoX.js";import"./Loader-1VreoqJz.js";import"./index-B4z8r-Ct.js";import"./createReactComponent-CwEnMXT7.js";function q({data:t}){return[{title:`${t==null?void 0:t.actionTitle} | JIVAS Manager`}]}async function M({request:t}){const i=(await t.formData()).get("agentId");return localStorage.setItem("jivas-agent",i),{}}function b(t){return t.replace(/\\/g,"\\\\").replace(/`/g,"\\`").replace(/\${/g,"\\${")}async function U({serverLoader:t,params:o}){var a,l,p,c;const i=localStorage.getItem("jivas-host"),g=localStorage.getItem("jivas-root-id"),f=localStorage.getItem("jivas-token"),u=localStorage.getItem("jivas-token-exp"),s=localStorage.getItem("jivas-agent"),r=await d(`${i}/walker/get_action`,{method:"POST",body:JSON.stringify({agent_id:s,action_id:o.actionId,reporting:!0}),headers:{"Content-Type":"application/json"}}).then(n=>n.json()),_=await d(`${i}/walker/get_action_app`,{method:"POST",body:JSON.stringify({agent_id:s,action:r.reports[0].label,reporting:!0}),headers:{"Content-Type":"application/json"}}).then(n=>n.json()).then(n=>{var m;return((m=n.reports)==null?void 0:m[0])||""}),y=`
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

${b(_.replaceAll("jvcli.client","jvclient").replaceAll("`","'"))}


root_id = "${g||""}"
print("ROOT ID:", root_id)
st.session_state.ROOT_ID = root_id or "000000000000000000000000"
st.session_state.TOKEN = "${f}"
st.session_state.EXPIRATION = ${u||0xe674660f0edc}


if __name__ == "__main__":
    router = StreamlitRouter()
    os.environ["JIVAS_BASE_URL"] = "${i||"http://localhost:8000"}";


    agent_id = "${s}"
    action_id = "${o.actionId}"

    info = json.loads('${JSON.stringify(r.reports[0]._package)}')

    render(router, agent_id, action_id, info)
    `}["streamlit_app.py"]}\`,
        },
      },
      document.getElementById("root"))
    <\/script>
  </body>
  </html>
					`;return{actionTitle:((c=(p=(l=(a=r==null?void 0:r.reports)==null?void 0:a[0])==null?void 0:l._package)==null?void 0:p.meta)==null?void 0:c.title)||"Action App",code:y}}const V=j(function({loaderData:o}){return e.jsxs(h,{px:"xl",py:"xl",children:[e.jsxs(I,{children:[e.jsx(x,{color:"dark",size:"sm",component:v,to:"./..",children:e.jsx(S,{})}),e.jsx(A,{order:3,children:"Manage Action"})]}),e.jsx(w,{mt:"xs",mb:"xl"}),e.jsx(h,{px:"xl",py:"xl",h:"90vh",children:e.jsx("iframe",{style:{outline:"none",border:"none"},title:"Action Config",width:"100%",height:"100%",srcDoc:o.code})})]})});export{M as clientAction,U as clientLoader,V as default,q as meta};
