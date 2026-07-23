# topo Swagger Summary

- Swagger UI: http://127.0.0.1:18769/topo/swagger-ui.html#/
- Raw Swagger JSON: http://127.0.0.1:18769/topo/v2/api-docs
- Title: nsrep-topo
- Version: master-1.5.7
- Description: 拓扑编辑设计
- Host: 127.0.0.1:18769
- Base Path: /topo/
- Tag Count: 43
- Path Count: 302
- Operation Count: 337
- Definition Count: 138

## HTTP Method Stats

- DELETE: 38
- GET: 154
- PATCH: 6
- POST: 112
- PUT: 27

## Tag Stats

- 6所环境: 12
- VM脚本配置 (Vm Script Tmpl Controller): 7
- excel定义拓扑 (Excel Define Topology Controller): 2
- vlan段 (Segment Controller): 10
- 专用API.: 1
- 任务相关接口 (Task Controller): 5
- 全局控制 (Global Control Controller): 3
- 公用 (Public Controller): 6
- 内部服务调用 (Internal Controller): 16
- 分布式互联 (Distributed Route Controller): 2
- 分靶场 (Range Controller): 6
- 势力方 (Party Controller): 7
- 复制 (Copy Controller): 1
- 外部网络 (External Controller): 3
- 子网 (Subnet Controller): 1
- 实物设备 (Physical Controller): 5
- 工程 (Project Controller): 23
- 工程可用域 (Zone Controller): 5
- 工程配额 (Quota Controller): 1
- 拓扑编辑 (Topo Controller): 62
- 拓扑编辑-连线 (Link Controller): 2
- 拓扑编辑操作记录及回撤功能 (History Controller): 2
- 拓扑设计 (Topology Controller): 12
- 攻防工具|虚拟机 (Vm Controller): 5
- 替代deploy接口 (Deploy Api Controller): 17
- 校验 (Check Out Controller): 2
- 根据脚本创建拓扑 (Topo Script Controller): 4
- 模板 (Template Controller): 6
- 特殊接口(慎用) (Special Controller): 4
- 状态展示 (Status Show Controller): 1
- 端口 (Port Controller): 8
- 管理员专用接口 (Manager Controller): 28
- 统计 (Statistics Controller): 7
- 编辑配置 (Edit Controller): 3
- 网状拓扑 (Mesh Topology Controller): 1
- 网络检测任务 (Network Checking Task Controller): 7
- 网络检测项 (Network Checking Item Controller): 10
- 网络自动配置 (Auto Controller): 9
- 虚拟机脚本的配置和下发 (Router Script Controller): 12
- 记录 (Note Controller): 3
- 设备查询 (Device Controller): 7
- 资源库中防火墙策略 (Fw Policy Controller): 8
- 资源库中防火墙规则 (Fw Rule Controller): 5
- 部署控制 (Deploy Control Controller): 3
- 部署记录 (Deploy Record Controller): 6

## Range APIs

- `POST /range/IPSecVPN`: 配置IPSecVPN
  params: dto(body,required)
- `POST /range/IPSecVPN/delete`: 删除IPSecVPN
  params: dto(body,required)
- `POST /range/import`: 生成工程拓扑并申请部署资源
  params: rangeTopoDTO(body,required)
- `GET /range/project/{projectId}`: 根据主靶场工程ID和分靶场ID获取分靶场工程ID
  params: projectId(path,required); rangeId(query,optional)
- `POST /range/project/{projectId}`: 手工录入工程绑定信息
  params: projectId(path,required); rangeId(query,optional); rangeProjectId(query,optional)
- `POST /range/projects/{projectId}/deploy`: 资源已占用直接部署
  params: projectId(path,required)

## Full API List

### 6所环境
- Operation Count: 12

- `POST /auto/project/{projectId}/network/{networkId}/vms`: 随机修改虚拟机或复制虚拟机
  operationId: `autoChangeVmUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /port/projects/{projectId}/list`: 工程端口列表
  operationId: `projectPortsUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; vmName[query,string,optional]; ip[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/arms/projects`: 查询应用攻防工具的工程
  operationId: `getProjectsUsingGET`
  params: toolIds[query,array,required]; pageSize[query,integer,optional]; page[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/arms/{projectId}/`: 查询工程攻防工具
  operationId: `getArmsUsingGET`
  params: projectId[path,string,required]; id[query,string,optional]; toolId[query,integer,optional]; toolName[query,string,optional]; networkId[query,string,optional]; page[query,integer,optional]; pageSize[query,integer,optional]; hasDevices[query,boolean,optional]; hasToolInfo[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /project/arms/{projectId}/{networkId}`: 拖拽攻防工具到topo
  operationId: `saveArmsUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /project/node/{mac}`: 根据mac地址查询设备信息
  operationId: `getNodeUsingGET`
  params: mac[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/findNodeMacByIp`: 根据ip地址查询设备mac
  operationId: `getMacByIpUsingGET`
  params: projectId[path,string,required]; ip[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/mac`: 工程下节点mac地址列表
  operationId: `getMacUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/node/{id}`: 节点详情及接入信息
  operationId: `getPositionInfoUsingGET`
  params: projectId[path,string,required]; id[path,string,required]; testId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /tmpl/{id}/train_data`: 获取工程模板中训练配置需要的信息
  operationId: `getTrainDataUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /tmpl/{id}/train_data/cache`: 清除对工程模板中训练配置需要的信息的缓存
  operationId: `clearTrainDataCacheUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /topo/projects/{projectId}/layout3D/scatter`: 3D展示节点散点图
  operationId: `getElementsForScatterUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### VM脚本配置
- Controller: Vm Script Tmpl Controller
- Operation Count: 7

- `DELETE /manage/scriptTmpl`: 批量删除
  operationId: `delBatchUsingDELETE`
  params: ids[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /manage/scriptTmpl/page`: 分页查询
  operationId: `serachUsingGET`
  params: id[query,integer,optional]; deviceType[query,string,optional]; type[query,string,optional]; imageId[query,string,optional]; page[query,integer,optional]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/scriptTmpl/save`: 新增
  operationId: `addScriptUsingPOST`
  params: scriptTmpl[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /manage/scriptTmpl/{id}`: 删除
  operationId: `delByIdUsingDELETE`
  params: id[path,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /manage/scriptTmpl/{id}`: 根据ID查询
  operationId: `findScriptUsingGET`
  params: id[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /manage/scriptTmpl/{id}`: 修改
  operationId: `updateUsingPUT_3`
  params: id[path,integer,required]; scriptTmpl[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /topo/scriptTmpl/list`: 查询设备可用模板列表
  operationId: `listUsingGET`
  params: id[query,integer,optional]; deviceType[query,string,optional]; type[query,string,optional]; imageId[query,string,optional]; page[query,integer,optional]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### excel定义拓扑
- Controller: Excel Define Topology Controller
- Operation Count: 2

- `POST /excel/define/topo/generate`: 上传excel文件生成工程
  operationId: `generateUsingPOST`
  params: file[formData,file,optional]; mode[query,string,optional]
  consumes: multipart/form-data
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /excel/define/topo/template`: 下载excel模板文件
  operationId: `downloadUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### vlan段
- Controller: Segment Controller
- Operation Count: 10

- `GET /segment/segments/{id}/subnets`: 查询该vlan段包含的子网
  operationId: `getSubnetsBySegmentIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /segment/{projectId}/{networkId}`: 新增vlan
  operationId: `saveSegmentationUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; segmentIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /segment/{projectId}/{networkId}/device/{deviceId}/bindingSegments`: 设备解绑vlan
  operationId: `deleteBindingSegmentUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]; ids[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /segment/{projectId}/{networkId}/device/{deviceId}/bindingSegments`: 设备绑定vlan
  operationId: `bindingSegmentUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]; ids[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /segment/{projectId}/{networkId}/segment/{id}`: 删除vlan
  operationId: `delSegmentationUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /segment/{projectId}/{networkId}/segment/{id}`: 查询vlan
  operationId: `getSegmentationUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /segment/{projectId}/{networkId}/segment/{id}`: 修改vlan
  operationId: `updateSegmentationUsingPUT`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; segmentIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /segment/{projectId}/{networkId}/segments/device/{deviceId}/available`: 查询可选vlan
  operationId: `getAvailableSegmentsUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /segment/{projectId}/{networkId}/segments/device/{deviceId}/binding`: 查询该设备已绑定的vlan
  operationId: `getUsedSegmentsUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /segment/{projectId}/{networkId}/segments/{id}/subnets`: 查询该vlan段包含的子网
  operationId: `getSubnetsBySegmentIdUsingGET_1`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 专用API.
- Operation Count: 1

- `POST /topo/projects/{projectId}/networks/{networkId}/fuckerPosition`: 根据指定参数快速生成服务器节点
  operationId: `quickCreateVmUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 任务相关接口
- Controller: Task Controller
- Operation Count: 5

- `POST /projects/{projectId}/bind/subject`: 工程绑定科目
  operationId: `bindUsingPOST`
  params: projectId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/build`: 构建完成
  operationId: `buildUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/ready`: 就绪
  operationId: `projectReadyUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /projects/{projectId}/task`: 获取任务
  operationId: `getTaskUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /projects/{projectId}/unbind/subject`: 工程解绑科目
  operationId: `unbindUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 全局控制
- Controller: Global Control Controller
- Operation Count: 3

- `DELETE /manage/global/control`: 解除控制
  operationId: `deleteControlUsingDELETE`
  params: key[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /manage/global/control`: 查询已有控制
  operationId: `getControlsUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/global/control`: 增加控制
  operationId: `addControlUsingPOST`
  params: in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 公用
- Controller: Public Controller
- Operation Count: 6

- `GET /public/networks`: 分页查询公共网络
  operationId: `findPublicNetworksUsingGET_1`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; networkType[query,string,optional]; tag[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /public/networks/{id}`: 根据id查询公共网络
  operationId: `findPublicNetworksUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /public/subnets`: 分页查询公共子网
  operationId: `findPublicSubnetsUsingGET_1`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; enableDhcp[query,boolean,optional]; networkId[query,string,optional]; ipVersion[query,integer,optional]; gatewayIp[query,string,optional]; cidr[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /public/subnets/{id}`: 根据id查询公共子网
  operationId: `findPublicSubnetsUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /public/subnets/{subnetId}/ips`: 从公共子网的可用范围ip中自动获取一个ip
  operationId: `getIpFromPublicSubnetUsingGET`
  params: subnetId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /public/subnets/{subnetId}/ips/{count}`: 从公共子网的可用范围ip中自动获取一定数量的ip|不足时不报错，由调用方验证
  operationId: `getIpsFromPublicSubnetUsingGET`
  params: subnetId[path,string,required]; count[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 内部服务调用
- Controller: Internal Controller
- Operation Count: 16

- `GET /internal/getTemplateData`: 获取脚本模板数据
  operationId: `getTemplateUsingGET`
  params: projectId[query,string,optional]; taskId[query,string,optional]; bindId[query,string,optional]; stageId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /internal/nodes/{nodeId}`: 根据id查询节点信息
  operationId: `getNodeUsingGET_1`
  params: nodeId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PATCH /internal/nodes/{nodeId}/change-physical`: 修改实物节点的绑定的实物设备并同步修改vlan号
  operationId: `updatePhysicalUsingPATCH`
  params: nodeId[path,string,required]; changePhysical[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `DELETE /internal/physicals/{physicalId}/release`: 强制释放占用的实物设备
  operationId: `releaseUsedPhysicalUsingDELETE`
  params: physicalId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /internal/project/range_project/{rangeProjectId}`: 根据分靶场信息查询本靶场工程
  operationId: `getProjectIdByRangeProjectIdUsingGET`
  params: rangeProjectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /internal/projects/{projectId}/id_map`: 获取新旧id关系
  operationId: `getIdMapUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /internal/projects/{projectId}/rangeItems`: 根据当前靶场元素的id查询分靶场对于的id
  operationId: `getRangeItemsByLocalIdsUsingPOST`
  params: projectId[path,string,required]; rangeId[query,string,optional]; localIds[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /internal/reserved_ip_addresses`: 校验ip并在云中添加预留ip
  operationId: `reservedIpAddressUsingPOST`
  params: in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /internal/reserved_ip_addresses/subnets/{subnetId}/ipaddresses/{ipAddress}`: 删除预留ip
  operationId: `deleteReservedIpAddressUsingDELETE`
  params: subnetId[path,string,required]; ipAddress[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /internal/template/check`: 校验脚本模板
  operationId: `checkTemplateUsingPOST`
  params: templateCheckIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /internal/template/export`: 导出工程模板
  operationId: `exportTemplateUsingGET`
  params: taskId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /internal/template/import`: 导入工程模板
  operationId: `importTemplateUsingPOST`
  params: importTemplate[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /internal/template/import/file`: 导入工程模板
  operationId: `importTemplateFileUsingPOST`
  params: file[formData,file,required]
  consumes: multipart/form-data
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /internal/tmpl/getTmplData/{id}`: 将工程或设备保存到模板
  operationId: `getTmplDataUsingGET`
  params: id[path,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /internal/vm/{vmId}/metadata`: 修改虚拟机元数据
  operationId: `findStaticRoutePromptUsingPUT`
  params: vmId[path,string,required]; metadataIn[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PATCH /internal/vm/{vmId}/password`: 修改虚拟机密码(仅改库)
  operationId: `changePasswordUsingPATCH`
  params: vmId[path,string,required]; vmAccout[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

### 分布式互联
- Controller: Distributed Route Controller
- Operation Count: 2

- `GET /config/info`: getConfigInfo
  operationId: `getConfigInfoUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /{projectId}/topo_and_intercon`: sendTopoDeployedAndInterconnectMsg
  operationId: `sendTopoDeployedAndInterconnectMsgUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 分靶场
- Controller: Range Controller
- Operation Count: 6

- `POST /range/IPSecVPN`: 配置IPSecVPN
  operationId: `configIPSecVPNUsingPOST`
  params: dto[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /range/IPSecVPN/delete`: 删除IPSecVPN
  operationId: `deleteIPSecVPNUsingPOST`
  params: dto[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /range/import`: 生成工程拓扑并申请部署资源
  operationId: `importTopoAndApplySourceUsingPOST`
  params: rangeTopoDTO[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /range/project/{projectId}`: 根据主靶场工程ID和分靶场ID获取分靶场工程ID
  operationId: `getRangeProjectUsingGET`
  params: projectId[path,string,required]; rangeId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /range/project/{projectId}`: 手工录入工程绑定信息
  operationId: `configRangeProjectIdUsingPOST`
  params: projectId[path,string,required]; rangeId[query,string,optional]; rangeProjectId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /range/projects/{projectId}/deploy`: 资源已占用直接部署
  operationId: `deployWithNotApplySourceUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 势力方
- Controller: Party Controller
- Operation Count: 7

- `GET /parties`: 查询势力方列表
  operationId: `findPartysUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,integer,optional]; name[query,string,optional]; alpha[query,integer,optional]; projectId[query,string,optional]; creator[query,string,optional]; enableUsed[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /parties/{id}`: 根据id查询势力方
  operationId: `findPartyByIdUsingGET`
  params: id[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /party/{projectId}`: 查询工程势力方分布情况
  operationId: `findPartyUseUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /projects/{projectId}/networks/{networkId}/parties/{id}`: 修改子网络下节点绑定的势力方
  operationId: `updateNodePartyUnderNetworkUsingPUT`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/parties`: 新增势力方
  operationId: `addPartyUsingPOST`
  params: projectId[path,string,required]; partyIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /projects/{projectId}/parties/{id}`: 删除势力方
  operationId: `deletePartyUsingDELETE`
  params: projectId[path,string,required]; id[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /projects/{projectId}/parties/{id}`: 修改势力方
  operationId: `updatePartyUsingPOST`
  params: projectId[path,string,required]; id[path,integer,required]; partyIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 复制
- Controller: Copy Controller
- Operation Count: 1

- `POST /projects/{projectId}/networks/{networkId}/copy`: 复制网络
  operationId: `copyVmUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 外部网络
- Controller: External Controller
- Operation Count: 3

- `GET /external/networks`: 查询外部网络列表
  operationId: `findNetworksUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /external/subnets`: 查询外部子网列表
  operationId: `findNetworksUsingGET_1`
  params: networkId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /external/synchronize/pull`: 同步os外部网络到本地
  operationId: `pullExternalUsingPOST`
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 子网
- Controller: Subnet Controller
- Operation Count: 1

- `GET /subnets/{id}/ips/{count}`: 获取可用ip
  operationId: `getAvailableIpsUsingGET`
  params: id[path,string,required]; count[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 实物设备
- Controller: Physical Controller
- Operation Count: 5

- `DELETE /physicals/indirect/nodes/{id}/accesses`: 删除已配置的非虚实互联实物设备的接入信息
  operationId: `deleteConfiguredAccessesForIndirectPhysicalUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /physicals/indirect/nodes/{id}/accesses`: 查询已配置的非虚实互联实物设备的接入信息
  operationId: `getConfiguredAccessesForIndirectPhysicalUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /physicals/indirect/nodes/{id}/accesses`: 配置非虚实互联实物设备的接入信息
  operationId: `configAccessesForIndirectPhysicalUsingPOST`
  params: id[path,string,required]; accessConfigIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /physicals/indirect/nodes/{id}/linked/ports`: 查询相连的虚实互联节点的端口信息
  operationId: `findLinkedDirectPhysicalPortsUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /physicals/{id}/use_info`: 查询指定实物设备使用情况
  operationId: `getUseInfoForPhysicalUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 工程
- Controller: Project Controller
- Operation Count: 23

- `POST /project/clear/{projectId}`: 清空工程中所有已部署设备
  operationId: `clearProjectUsingPOST_1`
  params: projectId[path,string,required]; force[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /project/delete/{projectId}`: 根据id删除工程
  operationId: `deleteProjectUsingDELETE_1`
  params: projectId[path,string,required]; force[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /project/getAllDevices/{projectId}`: 获取工程下所有设备信息
  operationId: `getAllDevicesUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /project/import/async`: 创建工程或异步导入工程
  operationId: `importProjectAsyncUsingPOST`
  params: templateId[query,string,optional]; mode[query,string,optional]; flag[query,string,optional]; projectIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /project/share/users/{projectId}`: 查询工程共享人
  operationId: `findShareUsersUsingGET_1`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /project/shareMyProject/{projectId}`: 分享工程
  operationId: `shareMyProjectUsingPOST_1`
  params: projectId[path,string,required]; userIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /project/update`: 修改工程信息
  operationId: `updateProjectUsingPOST`
  params: projectIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /project/{projectId}`: 根据id查询工程
  operationId: `findProjectByIdUsingGET`
  params: projectId[path,string,required]; onlyVmCount[query,boolean,optional]; getActions[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/devices/status`: 查询工程下设备及状态
  operationId: `findDeviceStatusUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /project/{projectId}/kickOut`: 踢出工程的分享人
  operationId: `kickOutUserUsingDELETE_1`
  params: projectId[path,string,required]; userIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /projects`: 分页查询工程列表
  operationId: `findProjectsForPageUsingGET_1`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; cloudName[query,string,optional]; status[query,integer,optional]; startTime[query,string,optional]; endTime[query,string,optional]; creator[query,string,optional]; member[query,string,optional]; enableAll[query,boolean,optional]; companyId[query,string,optional]; onlyVmCount[query,boolean,optional]; trainId[query,integer,optional]; taskId[query,string,optional]; taskName[query,string,optional]; phaseId[query,string,optional]; phaseName[query,string,optional]; subjectId[query,string,optional]; subjectName[query,string,optional]; bindId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /projects/deploying/{deployId}/cancel`: 取消部署
  operationId: `cancelDeployingUsingPOST`
  params: deployId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /projects/sort/sourceUsed`: 根据资源占用情况给工程排序
  operationId: `projectsSortedBySourceUsedUsingGET`
  params: sortBy[query,string,optional]; order[query,string,optional]; limit[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/sort/vm`: 根据虚拟机总个数/成功个数/失败个数给工程排序
  operationId: `projectsSortedByVmUsingGET`
  params: sortBy[query,string,optional]; order[query,string,optional]; limit[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/status/count`: 统计各状态工程的个数
  operationId: `getProjectStatusCountUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /projects/{id}/lock`: 锁定工程
  operationId: `lockProjectUsingPOST_1`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{id}/unlock`: 解锁工程
  operationId: `unlockProjectUsingPOST_1`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/deploy/async`: 部署工程-异步
  operationId: `deployProjectAsyncUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /projects/{projectId}/flavors/used`: 查询工程下flavor使用量
  operationId: `findFlavorsUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/{projectId}/images`: 查询工程下的镜像
  operationId: `findImagesUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/{projectId}/range/projects`: 查询下级靶场下的工程
  operationId: `getRangeProjectsUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /projects/{projectId}/topo/check`: topo校验
  operationId: `topoCheckUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/vms/destroy`: 销毁指定虚拟机
  operationId: `destroyVmsUsingPOST`
  params: projectId[path,string,required]; vmIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 工程可用域
- Controller: Zone Controller
- Operation Count: 5

- `GET /zones/project/{projectId}`: 查询工程可用域
  operationId: `saveZoneUsingGET`
  params: projectId[path,string,required]; zone[query,string,optional]; type[query,string,optional]; enableDefault[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /zones/project/{projectId}`: 新增工程可用域
  operationId: `saveZoneUsingPOST`
  params: projectId[path,string,required]; zoneIns[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /zones/project/{projectId}/zone`: 查询工程可用域使用情况
  operationId: `getZoneUseUsingGET`
  params: projectId[path,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /zones/project/{projectId}/zones/{id}`: 修改工程可用域是否是默认
  operationId: `saveZoneUsingPUT`
  params: projectId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /zones/{id}`: 删除可用域
  operationId: `deleteZoneUsingDELETE`
  params: id[path,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

### 工程配额
- Controller: Quota Controller
- Operation Count: 1

- `GET /quotas/{id}`: 查询工程配额
  operationId: `getQuotaTypeUsingGET`
  params: id[path,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 拓扑编辑
- Controller: Topo Controller
- Operation Count: 62

- `GET /topo/districts`: 查询地区列表
  operationId: `findDistrictsUsingGET`
  params: projectId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /topo/nodes/{nodeId}/attr`: 保存节点基本属性信息
  operationId: `updateNodeAttrUsingPUT`
  params: nodeId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/nodes/{nodeId}/binding_physical`: 绑定和解绑实物设备--仅拓扑配置
  operationId: `bindOrUnBindPhysicalDeviceUsingPOST`
  params: nodeId[path,string,required]; physicalId[query,string,optional]; physicalType[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PATCH /topo/nodes/{nodeId}/change-physical`: 修改实物节点的绑定的实物设备并同步修改vlan号
  operationId: `updatePhysicalUsingPATCH_1`
  params: nodeId[path,string,required]; changePhysical[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /topo/physical/ids`: 查询已使用的实物设备id列表
  operationId: `findPhysicalIdsUsingGET`
  params: projectId[query,string,optional]; type[query,string,optional]; id[query,array,optional]; allStatus[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/player-devices`: 查询选手设备信息
  operationId: `findPlayerDevicesUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; projectId[query,string,optional]; name[query,string,optional]; party[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/project/{projectId}/tree`: 查询当前工程下拓扑节点树
  operationId: `findTopoTreeUsingGET`
  params: projectId[path,string,required]; types[query,array,optional]; networkId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /topo/projects/{id}/auto_layout_2D/polyline`: 修改2D布局节点位置
  operationId: `updateAutoLayoutUsingPUT`
  params: id[path,string,required]; autoLayoutIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{id}/auto_layout_3D/hidden/networks`: 设置3D拓扑中隐藏的网络包含其下的所有节点
  operationId: `setHiddenNetworksFor3DUsingPOST`
  params: id[path,string,required]; networkIds[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{id}/auto_layout_3D/hidden/nodes`: 设置3D拓扑中隐藏的节点
  operationId: `setHiddenNodesFor3DUsingPOST`
  params: id[path,string,required]; nodeIds[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{id}/batch/vms/subnets`: 根据虚拟机id集合批量查询正在使用的子网信息
  operationId: `getSubnetsWithVmsUsedUsingPOST`
  params: id[path,string,required]; vmIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /topo/projects/{projectId}/auto_layout_3D`: 获取3D拓扑信息
  operationId: `getElementsFor3DUsingGET`
  params: projectId[path,string,required]; hasIp[query,boolean,optional]; hasVmStatus[query,boolean,optional]; ignoreXyzInLinks[query,boolean,optional]; hasOtherAttributes[query,boolean,optional]; screenConfigId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/auto_layout_3D/hidden`: 查询3D拓扑中隐藏的网络或节点
  operationId: `getHiddenFor3DUsingGET`
  params: projectId[path,string,required]; type[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /topo/projects/{projectId}/auto_layout_3D/out/levelRule`: 设置层级关系
  operationId: `getElementsFor3DOutUsingPUT`
  params: projectId[path,string,required]; levelRule[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PUT /topo/projects/{projectId}/batch/vms`: 批量修改虚拟机
  operationId: `batchUpdateUsingPUT`
  params: projectId[path,string,required]; attr[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /topo/projects/{projectId}/devices`: 查询设备列表
  operationId: `getDevicesUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; type[query,string,optional]; name[query,string,optional]; vmType[query,string,optional]; key[query,string,optional]; value[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/devices/search`: 指定工程或网络下设备名称模糊搜索
  operationId: `searchDevicesUsingGET`
  params: projectId[path,string,required]; networkId[query,string,optional]; name[query,string,optional]; ip[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/layout3D/scatter`: 3D展示节点散点图
  operationId: `getElementsForScatterUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/links/{linkId}`: 查询连线
  operationId: `getLinkInfoUsingGET`
  params: projectId[path,string,required]; linkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/networks/{networkId}/auto_layout_2D/nodes/{nodeId}/unfold`: 展开网络或集群节点到当前层网络,只适用于部分分层网络
  operationId: `unfoldNodeUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; nodeId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/containers`: 保存容器
  operationId: `saveContainerUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; containerIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PUT /topo/projects/{projectId}/networks/{networkId}/containers/merge`: 合并容器
  operationId: `mergeContainerUsingPUT`
  params: projectId[path,string,required]; networkId[path,string,required]; containerIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/cpoy`: 复制网络
  operationId: `copyVmUsingPOST_1`
  params: projectId[path,string,required]; networkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/fuckerPosition`: 根据指定参数快速生成服务器节点
  operationId: `quickCreateVmUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PATCH /topo/projects/{projectId}/networks/{networkId}/links`: 批量修改连线部分属性
  operationId: `updateLinksUsingPATCH`
  params: projectId[path,string,required]; networkId[path,string,required]; linkIns[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /topo/projects/{projectId}/networks/{networkId}/links`: 保存连线
  operationId: `saveLinkInfoUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; linkIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /topo/projects/{projectId}/networks/{networkId}/load_topology`: 加载拓扑图
  operationId: `loadTopologyUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; showType[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /topo/projects/{projectId}/networks/{networkId}/nodes/{nodeId}`: 根据节点id删除节点
  operationId: `deleteNodeByIdUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; nodeId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /topo/projects/{projectId}/networks/{networkId}/positions`: 保存节点位置
  operationId: `savePositionUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; positionIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/subnets`: 新增子网
  operationId: `saveSubnetUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; subnetIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /topo/projects/{projectId}/networks/{networkId}/subnets/{id}`: 删除子网
  operationId: `deleteSubnetUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `PUT /topo/projects/{projectId}/networks/{networkId}/subnets/{id}`: 修改子网
  operationId: `updateSubnetUsingPUT`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; enableDelete[query,boolean,optional]; subnetIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PUT /topo/projects/{projectId}/networks/{networkId}/subnets/{id}/check`: 检查dhcp服务（子网）是否可以修改
  operationId: `enableUpdateSubnetUsingPUT`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; subnetIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/targets/{id}`: 保存靶标节点信息
  operationId: `saveTargetUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/tests/{id}`: 保存试题节点信息
  operationId: `saveTestUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/three-layer-switches/{id}`: 保存三层交换机信息
  operationId: `saveTlSwitchUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; tlSwitchIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/tools/{id}`: 保存工具节点信息
  operationId: `saveToolUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/topology`: 保存本视图所有节点位置
  operationId: `saveTopologyJSONUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; topoJsonIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/vms/{id}`: 保存虚拟机信息
  operationId: `saveVmUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; vmIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/networks/{networkId}/vms/{vmId}/copy`: 复制主机
  operationId: `copyVmUsingPOST_2`
  params: projectId[path,string,required]; networkId[path,string,required]; vmId[path,string,required]; count[query,integer,required]; copyVmIn[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /topo/projects/{projectId}/node/filtering`: 根据条件过滤获取节点id
  operationId: `getNodeByFilteringUsingGET`
  params: projectId[path,string,required]; rangeId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /topo/projects/{projectId}/nodes`: 批量查询节点信息
  operationId: `getNodesUsingPOST`
  params: projectId[path,string,required]; nodeIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /topo/projects/{projectId}/nodes/{nodeId}`: 根据id查询节点信息
  operationId: `getNodeInfoUsingGET`
  params: projectId[path,string,required]; nodeId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/out/at`: 获取3D拓扑信息-对外提供-包含已部署信息
  operationId: `getAtDataUsingGET`
  params: projectId[path,string,required]; hasProjectName[query,boolean,optional]; hasSubnetInSwitch[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/projects/{projectId}/party/network`: 根据工程获取势力方网络信息
  operationId: `getPartyNetworkByProjectUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /topo/projects/{projectId}/targets/assign`: 清空已分配靶点
  operationId: `clearAssignedTargetsUsingDELETE`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /topo/projects/{projectId}/targets/assign`: 分配靶点
  operationId: `assignTargetsUsingPOST`
  params: projectId[path,string,required]; ins[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /topo/projects/{projectId}/targets/assign/cancel`: 取消分配靶点
  operationId: `cancelAssignTargetsUsingPOST`
  params: projectId[path,string,required]; ins[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /topo/projects/{project_id}/auto_layout_3D/hidden`: 取消在3d拓扑展示中隐藏了的节点或网络
  operationId: `deleteHiddenFor3DUsingDELETE`
  params: project_id[path,string,required]; type[query,string,optional]; id[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /topo/subnets/devices/{deviceId}`: 查询设备端口可用子网-分页
  operationId: `getSubnetsByDeviceIdUsingGET`
  params: deviceId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; segmentName[query,string,optional]; subnetName[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/subnets/links/{linkId}`: 查询双主机间或路由间的dhcp服务
  operationId: `findSubnetByLinkIdUsingGET`
  params: linkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/subnets/{id}`: 查询子网
  operationId: `findSubnetByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/vms`: 查询虚拟机列表
  operationId: `findVmsForPageUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; name[query,string,optional]; status[query,integer,optional]; startTime[query,string,optional]; endTime[query,string,optional]; clusterId[query,string,optional]; enableTmpl[query,boolean,optional]; projectId[query,string,optional]; vmType[query,string,optional]; imageName[query,string,optional]; flavorName[query,string,optional]; groupId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/{projectId}/attribute`: 查询工程下自定义属性
  operationId: `findAttibutesUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; networkId[query,string,optional]; name[query,string,optional]; key[query,string,optional]; value[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/{projectId}/attribute/key/{key}`: 查询工程下根据自定义属性key查value
  operationId: `findAttibuteValuesUsingGET`
  params: projectId[path,string,required]; key[path,string,required]; type[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/{projectId}/attribute/nodes`: 根据自定义属性查询节点
  operationId: `findNodesByAttibuteUsingGET`
  params: projectId[path,string,required]; id[query,string,optional]; key[query,string,optional]; value[query,string,optional]; type[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/{projectId}/attribute/nodes/key/{key}`: 根据自定义属性查询节点
  operationId: `findDeviceByAttibuteUsingGET`
  params: projectId[path,string,required]; key[path,string,required]; type[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/{projectId}/attribute/tree`: 查询工程下自定义属性
  operationId: `findAttibutesForTreeUsingGET`
  params: projectId[path,string,required]; networkId[query,string,optional]; type[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /topo/{projectId}/attribute/unique`: 查询工程下自定义属性 key-value去重
  operationId: `findAttibutesUniqueUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; networkId[query,string,optional]; name[query,string,optional]; key[query,string,optional]; value[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /topo/{projectId}/{networkId}/delContainer/{id}`: 删除容器
  operationId: `delContainerUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; enableDelNodes[query,boolean,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /topo/{projectId}/{networkId}/router/{routerId}/staticRoute/prompt`: 查询路由器静态路由相关信息
  operationId: `findStaticRoutePromptUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; routerId[path,string,required]; ipVersion[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /topo/{projectId}/{networkId}/vcs/{vcId}/vms/{vmId}/move`: 虚拟机移入集群
  operationId: `moveToVcUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; vcId[path,string,required]; vmId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 拓扑编辑-连线
- Controller: Link Controller
- Operation Count: 2

- `POST /projects/{projectId}/networks/{networkId}/links/stack`: 给多个交换机之间的连线配置成一个堆叠组
  operationId: `addStackUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; ids[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /projects/{projectId}/networks/{networkId}/links/stack/{stackId}`: 删除一个堆叠组
  operationId: `removeStackUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; stackId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

### 拓扑编辑操作记录及回撤功能
- Controller: History Controller
- Operation Count: 2

- `GET /edit/histories`: 查询工程的拓扑操作日志
  operationId: `findLogsForPageUsingGET`
  params: projectId[query,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /edit/histories/restore`: 回撤操作
  operationId: `restoreUsingPUT`
  params: projectId[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 拓扑设计
- Controller: Topology Controller
- Operation Count: 12

- `GET /checkName/{projectId}/{networkId}/{type}/{name}/{id}`: 校验设备名称是否重复
  operationId: `checkNameUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; type[path,string,required]; name[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /getNodeIdsInContainer/{containerIds}`: 查询容器中所有节点id
  operationId: `getNodeIdsInContainerUsingGET`
  params: containerIds[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /link/getIPsBylinkId/{linkId}`: 根据连线查询相关端口的ip
  operationId: `getIPsBylinkIdUsingGET`
  params: linkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /link/getLinksByNodeId/{nodeId}`: 查询节点的线
  operationId: `getLinksByNodeIdUsingGET`
  params: nodeId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /link/{projectId}/{networkId}/clearLinkPorts/{linkId}`: 清理连线上的端口
  operationId: `clearLinkPortsUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; linkId[path,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `PATCH /link/{projectId}/{networkId}/links`: 批量修改连线部分属性
  operationId: `updateLinksUsingPATCH_1`
  params: linkIns[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `DELETE /link/{projectId}/{networkId}/{id}`: 删除连线
  operationId: `deleteLInkByIdUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /saveFunction/{stageId}`: 保存拓扑中正在开启的功能
  operationId: `saveFunctionUsingGET`
  params: stageId[path,string,required]; functions[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /topo/{projectId}/clearTopo/{networkId}`: 清空当前拓扑图
  operationId: `clearTopoUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `DELETE /topo/{projectId}/{networkId}`: 批量删除节点,连线,容器
  operationId: `deleteUsingDELETE_3`
  params: projectId[path,string,required]; networkId[path,string,required]; ids[body,body,required]; enableDelNodes[query,boolean,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `DELETE /topo/{projectId}/{networkId}/removeDeviceFromContainer/{deviceId}`: 将某个设备从容器中剔除
  operationId: `removeDeviceFromContainerUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /{projectId}/{networkId}/savePosition`: 保存节点位置
  operationId: `savePositionUsingPOST_1`
  params: projectId[path,string,required]; networkId[path,string,required]; positionIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 攻防工具|虚拟机
- Controller: Vm Controller
- Operation Count: 5

- `GET /project/arms/projects`: 查询应用攻防工具的工程
  operationId: `getProjectsUsingGET`
  params: toolIds[query,array,required]; pageSize[query,integer,optional]; page[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/arms/{id}/devices`: getArmDevices
  operationId: `getArmDevicesUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/arms/{projectId}/`: 查询工程攻防工具
  operationId: `getArmsUsingGET`
  params: projectId[path,string,required]; id[query,string,optional]; toolId[query,integer,optional]; toolName[query,string,optional]; networkId[query,string,optional]; page[query,integer,optional]; pageSize[query,integer,optional]; hasDevices[query,boolean,optional]; hasToolInfo[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /project/arms/{projectId}/{networkId}`: 拖拽攻防工具到topo
  operationId: `saveArmsUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /vm/list/{projectId}`: 查询工程下虚拟机
  operationId: `findVmUsingGET`
  params: projectId[path,string,required]; vmIds[query,array,optional]; page[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; party[query,integer,optional]; networkId[query,string,optional]; creator[query,string,optional]; vmType[query,string,optional]; flavorId[query,string,optional]; host[query,string,optional]; hostIp[query,string,optional]; imageId[query,string,optional]; instance[query,string,optional]; sysType[query,string,optional]; zone[query,string,optional]; findPorts[query,boolean,optional]; enableDeployed[query,boolean,optional]; ip[query,string,optional]; hasQga[query,boolean,optional]; profile[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 替代deploy接口
- Controller: Deploy Api Controller
- Operation Count: 17

- `GET /deployed/physicals`: 查询已部署实物设备信息
  operationId: `getPhysicalsUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; projectId[query,string,optional]; networkId[query,string,optional]; networkName[query,string,optional]; creator[query,string,optional]; modifier[query,string,optional]; type[query,string,optional]; partyId[query,integer,optional]; ipAddress[query,string,optional]; macAddress[query,string,optional]; rangeId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /deployed/physicals`: 根据id批量查询已部署实物设备信息
  operationId: `getPhysicalByIdsUsingPOST`
  params: ids[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /deployed/physicals/{id}`: 查询已部署实物设备信息
  operationId: `getPhysicalByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/ports/{id}`: 查询已部署端口信息
  operationId: `getDeployedPortByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/projects/{projectId}/physicals`: 查询已部署实物设备信息
  operationId: `getDeployedPhysicalsUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; projectId[query,string,optional]; networkId[query,string,optional]; networkName[query,string,optional]; creator[query,string,optional]; modifier[query,string,optional]; type[query,string,optional]; partyId[query,integer,optional]; ipAddress[query,string,optional]; macAddress[query,string,optional]; rangeId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/projects/{projectId}/ports`: 工程端口列表
  operationId: `portsUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; projectId[query,string,optional]; subnetId[query,string,optional]; name[query,string,optional]; deviceId[query,string,optional]; deviceType[query,string,optional]; deviceName[query,string,optional]; ipAddress[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/projects/{projectId}/segments`: 工程网段(vlan)列表
  operationId: `segmentsUsingGET`
  params: projectId[path,string,required]; id[query,string,optional]; name[query,string,optional]; networkId[query,string,optional]; pageIndex[query,integer,required]; pageSize[query,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/projects/{projectId}/subnets`: 工程子网列表
  operationId: `subnetsUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; ipVersion[query,integer,optional]; networkId[query,string,optional]; projectId[query,string,optional]; segmentId[query,string,optional]; cloudId[query,string,optional]; status[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/projects/{projectId}/vms`: 虚拟机列表
  operationId: `vmsUsingGET`
  params: projectId[path,string,required]; vmTypes[query,array,optional]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; cloudId[query,string,optional]; projectId[query,string,optional]; projectName[query,string,optional]; cloudProjectName[query,string,optional]; instanceName[query,string,optional]; networkId[query,string,optional]; ipAddress[query,string,optional]; precisionIpAddress[query,string,optional]; macAddress[query,string,optional]; imageName[query,string,optional]; sysType[query,string,optional]; vmType[query,string,optional]; host[query,string,optional]; zone[query,string,optional]; partyId[query,integer,optional]; partyName[query,string,optional]; useId[query,string,optional]; useName[query,string,optional]; subnetId[query,string,optional]; rangeId[query,string,optional]; key[query,string,optional]; value[query,string,optional]; startTime[query,string,optional]; endTime[query,string,optional]; softName[query,string,optional]; sysVersion[query,string,optional]; performanceStatus[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/segments/{id}`: 查询已部署网段信息
  operationId: `getDeployedSegmentByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/subnets/{id}`: 查询已部署子网信息
  operationId: `getSubnetByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/vm/performanceStatus`: 查询虚拟机的效能状态(新)
  operationId: `getPerformanceStatusUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /deployed/vm/{vmId}/performanceStatus/{performanceStatus}`: 修改虚拟机的效能状态
  operationId: `updatePerformanceStatusUsingPUT`
  params: vmId[path,string,required]; performanceStatus[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /deployed/vms`: 分页查询已部署虚拟机信息
  operationId: `getVmsUsingGET`
  params: vmTypes[query,array,optional]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; cloudId[query,string,optional]; projectId[query,string,optional]; projectName[query,string,optional]; cloudProjectName[query,string,optional]; instanceName[query,string,optional]; networkId[query,string,optional]; ipAddress[query,string,optional]; precisionIpAddress[query,string,optional]; macAddress[query,string,optional]; imageName[query,string,optional]; sysType[query,string,optional]; vmType[query,string,optional]; host[query,string,optional]; zone[query,string,optional]; partyId[query,integer,optional]; partyName[query,string,optional]; useId[query,string,optional]; useName[query,string,optional]; subnetId[query,string,optional]; rangeId[query,string,optional]; key[query,string,optional]; value[query,string,optional]; startTime[query,string,optional]; endTime[query,string,optional]; softName[query,string,optional]; sysVersion[query,string,optional]; performanceStatus[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /deployed/vms`: 根据id集合批量查询已部署虚拟机信息
  operationId: `getVmsByIdsUsingPOST`
  params: ids[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /deployed/vms/{id}`: 查询已部署虚拟机信息
  operationId: `getVmByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /deployed/vms/{id}/addresses`: 查询已部署虚拟机端口信息
  operationId: `getAddressesUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 校验
- Controller: Check Out Controller
- Operation Count: 2

- `POST /projects/{projectId}/checkImage`: 校验当前工程所用镜像是否在资源库中可查
  operationId: `checkImagesIsAvailableUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/deploy/check`: 检验工程是否可以部署
  operationId: `checkOutProjectUsingPOST`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 根据脚本创建拓扑
- Controller: Topo Script Controller
- Operation Count: 4

- `POST /projects/json/async`: 根据脚本创建拓扑_异步
  operationId: `createProjectByJsonAsyncUsingPOST`
  params: readyDeploy[query,boolean,optional]; mode[query,string,optional]; topoScriptIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/json/async/file`: 根据脚本[文件]创建拓扑_异步
  operationId: `createProjectByJsonFileAsyncUsingPOST`
  params: readyDeploy[query,boolean,optional]; mode[query,string,optional]; file[formData,file,required]
  consumes: multipart/form-data
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/json/distribution`: 指定设备个数创建工程
  operationId: `distributeUsingPOST`
  params: readyDeploy[query,boolean,optional]; distributionIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/json/sync`: 根据脚本创建拓扑
  operationId: `createTopoByScriptJsonUsingPOST`
  params: readyDeploy[query,boolean,optional]; mode[query,string,optional]; topoScriptIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 模板
- Controller: Template Controller
- Operation Count: 6

- `POST /tmpl/convertToNew`: 将旧版模板数据转换成新版
  operationId: `convertToNewUsingPOST`
  params: in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /tmpl/projects/{projectId}/networks/{networkId}/templates/{id}/import`: 模板导入
  operationId: `importTmplToTopoUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]; mode[query,string,optional]; positionIn[body,body,optional]; targetInfoId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /tmpl/{id}/images_flavors`: 查询模板中用到的镜像和计算方案信息
  operationId: `getImagesAndFlavorsFromTemplateUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /tmpl/{id}/train_data`: 获取工程模板中训练配置需要的信息
  operationId: `getTrainDataUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /tmpl/{id}/train_data/cache`: 清除对工程模板中训练配置需要的信息的缓存
  operationId: `clearTrainDataCacheUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /tmpl/{projectId}/keys/{find}`: 查询工程设备id或key
  operationId: `keysUsingPOST`
  params: projectId[path,string,required]; find[path,string,required]; params[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 特殊接口(慎用)
- Controller: Special Controller
- Operation Count: 4

- `PATCH /special/addresses/cache`: 重新缓存虚拟机网卡信息
  operationId: `cacheAddressesUsingPATCH`
  params: projectId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /special/changeAllStatusInProject`: 强制修改指定工程下所有设备状态
  operationId: `changeStatusToDeployedUsingPOST`
  params: projectId[query,string,required]; status[query,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /special/projects/{projectId}/operations/{operation}/result/event/resend`: 重发工程操作事件结果消息
  operationId: `resendProjectOperationResultEventUsingPOST`
  params: projectId[path,string,required]; operation[path,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /special/projects/{projectId}/output/sql`: 导出工程数据为sql文件
  operationId: `outputProjectDataWithSqlUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 状态展示
- Controller: Status Show Controller
- Operation Count: 1

- `GET /projects/{projectId}/networks/{networkId}/status_show`: 查询当前拓扑网络中节点的展示状态
  operationId: `statusShowUsingGET`
  params: projectId[path,string,required]; networkId[path,string,required]; clusterId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 端口
- Controller: Port Controller
- Operation Count: 8

- `GET /port/projects/{projectId}/list`: 工程端口列表
  operationId: `projectPortsUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; vmName[query,string,optional]; ip[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /ports`: 查询端口
  operationId: `findPortsForPageUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; projectId[query,string,optional]; subnetId[query,string,optional]; name[query,string,optional]; deviceId[query,string,optional]; deviceType[query,string,optional]; deviceName[query,string,optional]; ipAddress[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /ports/devices/{deviceId}`: 查询指定设备的所有端口
  operationId: `findPortsByDeviceIdUsingGET`
  params: deviceId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /ports/{id}`: 根据端口id查询端口
  operationId: `findPortWebOutByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /projects/{projectId}/networks/{networkId}/ports`: 新增或修改端口
  operationId: `savePortUsingPOST_1`
  params: projectId[path,string,required]; networkId[path,string,required]; portIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /projects/{projectId}/networks/{networkId}/ports/changeIp`: 新增或修改端口|-仅限护网场景已改过虚拟机IP后使用
  operationId: `savePortUsingPOST`
  params: in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /projects/{projectId}/networks/{networkId}/ports/{id}`: 删除端口
  operationId: `deletePortUsingDELETE`
  params: projectId[path,string,required]; networkId[path,string,required]; id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /{projectId}/subnet/{subnetId}/ports`: 根据子网id查询端口
  operationId: `findPortsBySubnetIdUsingGET`
  params: projectId[path,string,required]; subnetId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; projectId[query,string,optional]; subnetId[query,string,optional]; name[query,string,optional]; deviceId[query,string,optional]; deviceType[query,string,optional]; deviceName[query,string,optional]; ipAddress[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 管理员专用接口
- Controller: Manager Controller
- Operation Count: 28

- `GET /manage/editConfig/project/find`: 查询初始化默认配置
  operationId: `findProjectEditConfigsUsingGET_1`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/editConfig/project/init`: 初始化默认配置
  operationId: `initProjectEditConfigsUsingPOST`
  params: projectEditConfigIns[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /manage/image_flows`: 流量镜像线信息
  operationId: `findImageFlowsUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; projectId[query,string,optional]; projectName[query,string,optional]; cloudProjectName[query,string,optional]; networkId[query,string,optional]; networkName[query,string,optional]; srcDeviceId[query,string,optional]; destDeviceId[query,string,optional]; srcDeviceName[query,string,optional]; destDeviceName[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /manage/os/count/log`: os网络历史个数统计
  operationId: `getOsCountLogUsingGET`
  params: days[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /manage/project/count`: 统计各状态工程个数
  operationId: `findProjectCountByStatusUsingGET`
  params: status[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /manage/project/delete/{projectId}`: 根据id删除工程
  operationId: `deleteProjectUsingDELETE`
  params: projectId[path,string,required]; force[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /manage/project/image_flavor/synchronize`: 同步镜像和计算方案信息
  operationId: `synchronizeImageFlavorDataUsingPOST`
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /manage/project/kickOut/{projectId}`: 踢出工程的分享人
  operationId: `kickOutUserUsingDELETE`
  params: projectId[path,string,required]; userIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /manage/project/list`: 分页查询工程列表
  operationId: `findProjectListUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; cloudName[query,string,optional]; status[query,integer,optional]; startTime[query,string,optional]; endTime[query,string,optional]; creator[query,string,optional]; member[query,string,optional]; enableAll[query,boolean,optional]; companyId[query,string,optional]; onlyVmCount[query,boolean,optional]; trainId[query,integer,optional]; taskId[query,string,optional]; taskName[query,string,optional]; phaseId[query,string,optional]; phaseName[query,string,optional]; subjectId[query,string,optional]; subjectName[query,string,optional]; bindId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/project/physical/synchronize`: 同步实物设备信息
  operationId: `synchronizePhysicalDataUsingPOST`
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /manage/project/share/users/{projectId}`: 查询工程共享人
  operationId: `findShareUsersUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/project/shareMyProject/{projectId}`: 分享工程
  operationId: `shareMyProjectUsingPOST`
  params: projectId[path,string,required]; userIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /manage/project/{projectId}/clearTask`: 清理任务控制
  operationId: `clearTaskUsingDELETE`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /manage/projects`: 分页查询工程列表
  operationId: `findProjectsForPageUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; cloudName[query,string,optional]; status[query,integer,optional]; startTime[query,string,optional]; endTime[query,string,optional]; creator[query,string,optional]; member[query,string,optional]; enableAll[query,boolean,optional]; companyId[query,string,optional]; onlyVmCount[query,boolean,optional]; trainId[query,integer,optional]; taskId[query,string,optional]; taskName[query,string,optional]; phaseId[query,string,optional]; phaseName[query,string,optional]; subjectId[query,string,optional]; subjectName[query,string,optional]; bindId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/projects/{id}/lock`: 锁定工程
  operationId: `lockProjectUsingPOST`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /manage/projects/{id}/unlock`: 解锁工程
  operationId: `unlockProjectUsingPOST`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /manage/projects/{projectId}/clear`: 清空工程
  operationId: `clearProjectUsingPOST`
  params: projectId[path,string,required]; type[query,string,optional]; force[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /manage/public/networks`: 新增公共网络
  operationId: `addPublicNetworksUsingPOST`
  params: publicNetworkIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /manage/public/networks/{id}`: 删除公共网络
  operationId: `deletePublicNetworksUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `PUT /manage/public/networks/{id}`: 修改公共网络
  operationId: `updatePublicNetworksUsingPUT`
  params: id[path,string,required]; publicNetworkIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /manage/public/networks/{id}/companies`: 给网络分配单位
  operationId: `assignCompaniesForPublicNetworkUsingPOST`
  params: id[path,string,required]; companyIds[body,body,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /manage/public/subnets`: 新增公共子网
  operationId: `addPublicSubnetsUsingPOST`
  params: publicSubnetIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /manage/public/subnets/{id}`: 删除公共子网
  operationId: `deletePublicSubnetsUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /manage/subnets`: 子网列表
  operationId: `findSubnetsUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; ipVersion[query,integer,optional]; networkId[query,string,optional]; projectId[query,string,optional]; segmentId[query,string,optional]; cloudId[query,string,optional]; status[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /manage/synchronize-company-resources`: 同步单位资源
  operationId: `synchronizeCompanyResourcesUsingPOST`
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /manage/tmpl/preview/{templateId}`: 根据模板Id查询模板数据
  operationId: `getTmplUsingGET`
  params: templateId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /manage/virtualType/count`: 统计不同虚拟化节点个数
  operationId: `findVirtualTypeCountUsingGET`
  params: projectId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /manage/vms`: 虚拟机列表
  operationId: `findVmsUsingGET`
  params: projectId[query,string,optional]; status[query,integer,optional]; name[query,string,optional]; page[query,integer,optional]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 统计
- Controller: Statistics Controller
- Operation Count: 7

- `GET /statistics/group/vm`: 根据不同分组统计已部署虚拟机个数
  operationId: `statisticVmCountWithGroupUsingGET`
  params: groupBy[query,string,required]; projectId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /statistics/projects`: 统计工程的各种状态的个数
  operationId: `statisticsProjectsUsingGET`
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /statistics/projects/sort/sourceUsed`: 根据资源占用情况给工程排序
  operationId: `projectsSortedBySourceUsedUsingGET_1`
  params: sortBy[query,string,optional]; order[query,string,optional]; limit[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /statistics/projects/sort/vm`: 根据虚拟机总个数/成功个数/失败个数给工程排序
  operationId: `projectsSortedByVmUsingGET_1`
  params: sortBy[query,string,optional]; order[query,string,optional]; limit[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /statistics/projects/{projectId}/range/group/sourceUsed`: 按靶场分组统计资源使用量
  operationId: `statisticSourceUsedByRangeUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /statistics/projects/{projectId}/resource/count`: 统计工程各资源的使用总量
  operationId: `getProjectResourceCountUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /statistics/projects/{projectId}/types/devices/count`: 根据设备分类，统计个数
  operationId: `getDeviceCountForTypeUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 编辑配置
- Controller: Edit Controller
- Operation Count: 3

- `GET /editConfig/project/find/{projectId}`: 查询工程配置列表
  operationId: `findProjectEditConfigsUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `DELETE /editConfig/project/reset/{projectId}`: 重置工程编辑配置
  operationId: `resetProjectEditConfigsUsingDELETE`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `POST /editConfig/project/save/{projectId}`: 增改工程编辑配置
  operationId: `addProjectEditConfigUsingPOST`
  params: projectId[path,string,required]; projectEditConfigIns[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 网状拓扑
- Controller: Mesh Topology Controller
- Operation Count: 1

- `POST /projects/{projectId}/networks/{networkId}/meshTopology/import`: 网状拓扑导入
  operationId: `importMeshTopologyUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 网络检测任务
- Controller: Network Checking Task Controller
- Operation Count: 7

- `GET /network_checking/tasks`: 查询任务信息
  operationId: `findTaskForPageUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,integer,optional]; name[query,string,optional]; projectId[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /network_checking/tasks`: 创建任务
  operationId: `createTaskUsingPOST`
  params: in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /network_checking/tasks/{taskId}`: 删除任务
  operationId: `deleteItemByIdUsingDELETE_1`
  params: taskId[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /network_checking/tasks/{taskId}`: 查询任务信息
  operationId: `getTaskByIdUsingGET`
  params: taskId[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /network_checking/tasks/{taskId}`: 修改任务
  operationId: `updateTaskUsingPUT`
  params: taskId[path,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /network_checking/tasks/{taskId}/start`: 开始任务
  operationId: `startTaskUsingPOST`
  params: taskId[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /network_checking/tasks/{taskId}/stop`: 停止任务
  operationId: `stopTaskUsingPOST`
  params: taskId[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 网络检测项
- Controller: Network Checking Item Controller
- Operation Count: 10

- `POST /network_checking/items/access`: 创建测试项--接入
  operationId: `createAccessItemUsingPOST`
  params: taskId[query,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /network_checking/items/network_reachable`: 创建测试项--网络可达
  operationId: `createNetworkReachableItemUsingPOST`
  params: taskId[query,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /network_checking/items/network_scan`: 创建测试项--网络ip扫描
  operationId: `createNetworkScanItemUsingPOST`
  params: taskId[query,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /network_checking/items/open_port`: 创建测试项--开放端口
  operationId: `createOpenPortItemUsingPOST`
  params: taskId[query,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /network_checking/items/{itemId}`: 删除测试项
  operationId: `deleteItemByIdUsingDELETE`
  params: itemId[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `PUT /network_checking/items/{itemId}/access`: 修改测试项--接入
  operationId: `updateAccessItemUsingPUT`
  params: itemId[path,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /network_checking/items/{itemId}/detail`: 查询测试项详细
  operationId: `findItemDetailByIdUsingGET`
  params: itemId[path,integer,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /network_checking/items/{itemId}/network_reachable`: 修改测试项--网络可达
  operationId: `updateNetworkReachableItemUsingPUT`
  params: itemId[path,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PUT /network_checking/items/{itemId}/network_scan`: 修改测试项--网络ip扫描
  operationId: `updateNetworkScanItemUsingPUT`
  params: itemId[path,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PUT /network_checking/items/{itemId}/open_port`: 修改测试项--开放端口
  operationId: `updateOpenPortItemUsingPUT`
  params: itemId[path,integer,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 网络自动配置
- Controller: Auto Controller
- Operation Count: 9

- `POST /auto/port/{projectId}/{deviceId}`: 自动配置端口
  operationId: `createPortUsingPOST`
  params: projectId[path,string,required]; deviceId[path,string,required]; enableDhcp[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /auto/project/{projectId}/asyn`: 工程网络自动化配置
  operationId: `configProjectUsingPOST`
  params: projectId[path,string,required]; deepSize[query,integer,optional]; routerConfig[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /auto/project/{projectId}/network/{networkId}/vms`: 随机修改虚拟机或复制虚拟机
  operationId: `autoChangeVmUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /auto/project/{projectId}/result`: 查询自动配置结果
  operationId: `getResultUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /auto/project/{projectId}/router/openvpn`: 公网路由切换openvpn脚本
  operationId: `switchOpenVpnUsingPOST`
  params: projectId[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /auto/router/{projectId}/{networkId}/{protocol}`: 生成路由脚本的用户数据
  operationId: `autoConfigRouteUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; protocol[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /auto/segment/{projectId}/{networkId}/{deviceId}`: 自动配置vlan
  operationId: `createSegmentUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /auto/subnet/{projectId}/{networkId}/link/{linkId}`: 自动配置VM或路由间子网
  operationId: `createLinkSubnetUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; linkId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /auto/subnet/{projectId}/{networkId}/{deviceId}`: 自动配置子网
  operationId: `createSubnetUsingPOST`
  params: projectId[path,string,required]; networkId[path,string,required]; deviceId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 虚拟机脚本的配置和下发
- Controller: Router Script Controller
- Operation Count: 12

- `GET /device_scripts`: 分页查询脚本
  operationId: `findForPageUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; type[query,string,optional]; name[query,string,optional]; projectId[query,string,required]; deviceId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /device_scripts`: 新增脚本
  operationId: `createUsingPOST`
  params: in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /device_scripts/batch`: 批量新增私有脚本,可立即下发
  operationId: `batchCreateUsingPOST`
  params: ins[body,body,required]; mode[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /device_scripts/devices/deployed`: 分页查询设备列表
  operationId: `findDevicesForPageUsingGET`
  params: vmTypes[query,array,optional]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; cloudId[query,string,optional]; projectId[query,string,optional]; projectName[query,string,optional]; cloudProjectName[query,string,optional]; instanceName[query,string,optional]; networkId[query,string,optional]; ipAddress[query,string,optional]; precisionIpAddress[query,string,optional]; macAddress[query,string,optional]; imageName[query,string,optional]; sysType[query,string,optional]; vmType[query,string,optional]; host[query,string,optional]; zone[query,string,optional]; partyId[query,integer,optional]; partyName[query,string,optional]; useId[query,string,optional]; useName[query,string,optional]; subnetId[query,string,optional]; rangeId[query,string,optional]; key[query,string,optional]; value[query,string,optional]; startTime[query,string,optional]; endTime[query,string,optional]; softName[query,string,optional]; sysVersion[query,string,optional]; performanceStatus[query,integer,optional]; showReady[query,boolean,optional]; showLastedRun[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /device_scripts/logs`: 查询下发日志
  operationId: `findLogsForPageUsingGET_1`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; scriptId[query,string,optional]; deviceId[query,string,optional]; projectId[query,string,required]; mode[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /device_scripts/run/dynamic_route`: 指定工程下自动配置下发
  operationId: `runForDynamicRouteUsingPOST`
  params: projectId[query,string,required]; mode[query,string,optional]; routingProtocol[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /device_scripts/run/private`: 私有脚本的下发
  operationId: `runPrivateReadyScriptUsingPOST`
  params: deviceIds[body,body,required]; mode[query,string,optional]; routingProtocol[query,string,optional]; autoGenerate[query,boolean,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /device_scripts/{id}`: 删除脚本
  operationId: `deleteUsingDELETE_2`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /device_scripts/{id}`: 查询脚本
  operationId: `findByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /device_scripts/{id}`: 修改脚本
  operationId: `updateUsingPUT_2`
  params: id[path,string,required]; in[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `PUT /device_scripts/{id}/ready`: 修改其中一个脚本为ready状态
  operationId: `readyUsingPUT`
  params: id[path,string,required]; deviceId[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `POST /device_scripts/{id}/run/public`: 公用脚本的下发
  operationId: `runPublicScriptUsingPOST`
  params: id[path,string,required]; deviceIds[body,body,required]; mode[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 记录
- Controller: Note Controller
- Operation Count: 3

- `DELETE /note/project/{projectId}`: 根据projectId删除
  operationId: `delByProjectIdUsingDELETE`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /note/project/{projectId}`: 根据工程查询
  operationId: `getUsingGET_1`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /note/project/{projectId}`: 保存记录
  operationId: `saveUsingPOST_1`
  params: projectId[path,string,required]; note[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 设备查询
- Controller: Device Controller
- Operation Count: 7

- `GET /project/flag-servers`: 查询flag服务器
  operationId: `findFlagServersUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; projectId[query,string,optional]; name[query,string,optional]; ip[query,string,optional]; rangeId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/node/{mac}`: 根据mac地址查询设备信息
  operationId: `getNodeUsingGET`
  params: mac[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/physicals`: 实物设备分页查询
  operationId: `findPhysicalsUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; projectId[query,string,optional]; networkId[query,string,optional]; networkName[query,string,optional]; creator[query,string,optional]; modifier[query,string,optional]; type[query,string,optional]; partyId[query,integer,optional]; ipAddress[query,string,optional]; macAddress[query,string,optional]; rangeId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/physicals/{id}`: 根据设备id查询实物设备信息
  operationId: `getPhysicalByIdUsingGET_1`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/findNodeMacByIp`: 根据ip地址查询设备mac
  operationId: `getMacByIpUsingGET`
  params: projectId[path,string,required]; ip[query,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/mac`: 工程下节点mac地址列表
  operationId: `getMacUsingGET`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /project/{projectId}/node/{id}`: 节点详情及接入信息
  operationId: `getPositionInfoUsingGET`
  params: projectId[path,string,required]; id[path,string,required]; testId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

### 资源库中防火墙策略
- Controller: Fw Policy Controller
- Operation Count: 8

- `GET /fw/policies`: 分页查询
  operationId: `findPoliciesUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; visibility[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /fw/policies`: 新增策略
  operationId: `saveUsingPOST`
  params: fwPolicyIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /fw/policies/{id}`: 删除策略
  operationId: `deleteUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /fw/policies/{id}`: 查询策略
  operationId: `findUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /fw/policies/{id}`: 修改策略
  operationId: `updateUsingPUT`
  params: id[path,string,required]; fwPolicyIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /fw/policies/{id}/rules`: 策略中移除规则
  operationId: `delRulesFromPolicyUsingDELETE`
  params: id[path,string,required]; ruleIds[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /fw/policies/{id}/rules`: 查询策略中的规则
  operationId: `findRulesFromPolicyUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /fw/policies/{id}/rules`: 策略中增加规则
  operationId: `addRulesToPolicyUsingPOST`
  params: id[path,string,required]; insertRule[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 资源库中防火墙规则
- Controller: Fw Rule Controller
- Operation Count: 5

- `GET /fw/rules`: 分页查询+条件防火墙规则列表
  operationId: `findRulesUsingGET`
  params: pageIndex[query,integer,optional]; pageSize[query,integer,optional]; sortBy[query,string,optional]; order[query,string,optional]; id[query,string,optional]; name[query,string,optional]; protocol[query,string,optional]; action[query,string,optional]; ipVersion[query,string,optional]; visibility[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `POST /fw/rules`: 保存防火墙规则
  operationId: `saveRuleUsingPOST`
  params: ruleIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `DELETE /fw/rules/{id}`: 根据id删除防火墙规则
  operationId: `deleteRuleByIdUsingDELETE`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 204, 401, 403

- `GET /fw/rules/{id}`: 根据id查询防火墙规则
  operationId: `findRuleByIdUsingGET`
  params: id[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /fw/rules/{id}`: 修改防火墙规则
  operationId: `updateRuleUsingPUT`
  params: id[path,string,required]; ruleIn[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 部署控制
- Controller: Deploy Control Controller
- Operation Count: 3

- `PUT /deploy_control/projects/{projectId}/vms/ready`: 设置未部署虚拟机下次是否可以部署--整个工程
  operationId: `updateVmReadyToDeployUsingPUT`
  params: projectId[path,string,required]; readyToDeploy[query,boolean,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /deploy_control/vms/ready`: 查询虚拟机是否准备部署的信息
  operationId: `findVmsWithReadyUsingGET`
  params: projectId[query,string,optional]; id[query,string,optional]; readyToDeploy[query,boolean,optional]; limit[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /deploy_control/vms/ready`: 设置未部署虚拟机下次是否可以部署
  operationId: `updateVmReadyToDeployUsingPUT_1`
  params: ins[body,body,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

### 部署记录
- Controller: Deploy Record Controller
- Operation Count: 6

- `GET /deploy/{deployId}/record`: 根据部署id查询某次部署记录
  operationId: `getDeployRecordByDeployIdUsingGET`
  params: deployId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/{projectId}/deploy/records`: 根据工程id查询工程部署记录
  operationId: `getDeployRecordsUsingGET`
  params: projectId[path,string,required]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/{projectId}/deploy/{deployId}/detail`: 根据部署ID查询工程部署进度的详细信息
  operationId: `getDeployDetailUsingGET`
  params: projectId[path,string,required]; deployId[path,string,required]; rangeId[query,string,required]; type[query,string,optional]; status[query,integer,optional]; pageIndex[query,integer,optional]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `GET /projects/{projectId}/deploy/{deployId}/summary`: 根据部署ID查询工程部署进度的粗略信息
  operationId: `getDeployDetailsClassificationUsingGET`
  params: projectId[path,string,required]; deployId[path,string,required]; rangeId[query,string,required]; pageSize[query,integer,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404

- `PUT /projects/{projectId}/deploying/refresh`: 尝试刷新工程总的部署进度
  operationId: `refreshDeployingUsingPUT`
  params: projectId[path,string,required]
  consumes: application/json
  produces: */*
  responses: 200, 201, 401, 403, 404

- `GET /projects/{projectId}/ranges`: 查询工程部署记录中的分靶场列表
  operationId: `getRangesUsingGET`
  params: projectId[path,string,required]; deployId[query,string,optional]
  consumes: application/json
  produces: */*
  responses: 200, 401, 403, 404
