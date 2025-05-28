const { Plugin } = require('blockbench-types')

const modpackFixPlugin = new Plugin('modpackFix', {
    name: 'Modpack Fix Integration',
    author: 'p4tit0',
    description: 'Integration with modpack-fix tool',
    version: '1.0.0',
    tags: ['Minecraft', 'Modding'],
    
    onload() {
        const socket = require('socket.io-client')('http://localhost:3000')
        
        socket.on('load_model', (data) => {
            Blockbench.showQuickMessage(`Loading ${data.name}...`)
            Blockbench.loadModel(JSON.parse(data.model), data.type, data.name)
        })
    }
})

module.exports = modpackFixPlugin