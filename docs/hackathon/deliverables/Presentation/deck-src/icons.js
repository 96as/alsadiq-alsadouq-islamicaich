const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),sharp=require('sharp'),fa=require('react-icons/fa6');
const names=process.argv.slice(2);
const colors={turq:'#2EF2C2',white:'#F2F4FF',muted:'#8E99CC'};
(async()=>{for(const n of names){const C=fa[n];if(!C){console.log('MISSING',n);continue}
for(const [k,c] of Object.entries(colors)){const svg=renderToStaticMarkup(React.createElement(C,{size:512,color:c}));
await sharp(Buffer.from(svg)).resize(384,384,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}}).png().toFile(`icons/${n}-${k}.png`);}}console.log('done')})();
