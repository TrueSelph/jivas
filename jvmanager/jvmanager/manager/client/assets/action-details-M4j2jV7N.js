import{w as g,z as f}from"./chunk-QMGIS6GS-CBZUm-7V.js";import{j as t}from"./jsx-runtime-D_zvdyIk.js";import{f as l}from"./api-tgDzxHzW.js";import{B as c}from"./polymorphic-factory-EW0USS3V.js";import{G as u}from"./Group-bnACpcuK.js";import{A as _}from"./ActionIcon-BO4DDcDR.js";import{I as y}from"./IconArrowLeft-4qKQ7vAI.js";import{T as j}from"./Title-B0fFn55O.js";import{D as v}from"./Divider-BI4N1hoX.js";import"./Loader-1VreoqJz.js";import"./index-B4z8r-Ct.js";import"./createReactComponent-CwEnMXT7.js";async function P({request:e}){const i=(await e.formData()).get("agentId");return localStorage.setItem("jivas-agent",i),{}}function I(e){return e.replace(/\//g,"\\/").replace(/`/g,"\\`").replace(/\${/g,"\\${ ")}async function L({serverLoader:e,params:o}){const i=localStorage.getItem("jivas-host"),p=localStorage.getItem("jivas-root-id"),m=localStorage.getItem("jivas-token"),d=localStorage.getItem("jivas-token-exp"),n=localStorage.getItem("jivas-agent"),a=await l(`${i}/walker/get_action`,{method:"POST",body:JSON.stringify({agent_id:n,action_id:o.actionId,reporting:!0}),headers:{"Content-Type":"application/json"}}).then(r=>r.json()),h=await l(`${i}/walker/get_action_app`,{method:"POST",body:JSON.stringify({agent_id:n,action:a.reports[0].label,reporting:!0}),headers:{"Content-Type":"application/json"}}).then(r=>r.json()).then(r=>{var s;return((s=r.reports)==null?void 0:s[0])||""});return`${I(h.replaceAll("jvcli.client","jvclient").replaceAll("`","'"))}${p||""}${m}${d||0xe674660f0edc}${i||"http://localhost:8000"}${n}${o.actionId}${JSON.stringify(a.reports[0]._package)}`,{code:`
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
          "streamlit_app.py":
        },
      },
      document.getElementById("root"))
    <\/script>
  </body>
  </html>
				`}}const J=g(function({loaderData:o}){return t.jsxs(c,{px:"xl",py:"xl",children:[t.jsxs(u,{children:[t.jsx(_,{color:"dark",size:"sm",component:f,to:"./..",children:t.jsx(y,{})}),t.jsx(j,{order:3,children:"Manage Action"})]}),t.jsx(v,{mt:"xs",mb:"xl"}),t.jsx(c,{px:"xl",py:"xl",h:"90vh",children:t.jsx("iframe",{style:{outline:"none",border:"none"},title:"Action Config",width:"100%",height:"100%",srcDoc:o.code})})]})});export{P as clientAction,L as clientLoader,J as default};
