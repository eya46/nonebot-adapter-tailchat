from abc import ABC
from typing import Any, Literal, Union

from nonebot.adapters import Bot as BaseBot
from pydantic import TypeAdapter

from .const import Optional, Undefined
from .model import (
    Ack,
    AddFriendRequestRet,
    BaseGroupInfo,
    BotInfoRet,
    ClientConfig,
    ConverseInfo,
    FindAndJoinRoomRet,
    GroupAndPanelIds,
    GroupDataRet,
    GroupInfo,
    Health,
    InviteCodeInfo,
    LastMessages,
    MessageMetaDict,
    MessageRet,
    Panel,
    TemporaryUserInfo,
    TokenInfo,
    UserInfo,
    Whoami,
)


class API(BaseBot, ABC):
    async def allAck(self) -> list[Ack]:
        """获取所有会话的最后一条消息的ID"""
        return TypeAdapter(list[Ack]).validate_python(await self.call_api("chat.ack.all"))

    async def allApp(self):
        """获取当前账号全部openapi app信息"""
        return await self.call_api("openapi.app.all")

    async def getApp(self, *, appId: str):
        """获取openapi app信息"""
        return await self.call_api("openapi.app.get", appId=appId)

    async def whoami(self) -> Whoami:
        """获取当前账户信息"""
        return TypeAdapter(Whoami).validate_python(await self.call_api("user.whoami"))

    async def getFile(self, *, objectName: str):
        """获取客户端的信息"""
        return await self.call_api("file.get", objectName=objectName)

    async def ackInbox(self, *, inboxItemIds: list[str]) -> bool:
        """标记消息为已读"""
        return await self.call_api("chat.inbox.ack", inboxItemIds=inboxItemIds)

    async def allInbox(self) -> MessageRet:
        """获取用户收件箱中所有内容"""
        return TypeAdapter(MessageRet).validate_python(await self.call_api("chat.inbox.all"))

    async def isMember(self, *, groupId: str):
        """是否为指定群的成员"""
        return await self.call_api("group.isMember", groupId=groupId)

    async def register(
        self,
        *,
        password: str,
        email: Optional[str] = Undefined,
        avatar: Optional[str] = Undefined,
        emailOTP: Optional[str] = Undefined,
        nickname: Optional[str] = Undefined,
        username: Optional[str] = Undefined,
    ):
        """用户注册"""
        return await self.call_api(
            "user.register",
            email=email,
            avatar=avatar,
            emailOTP=emailOTP,
            nickname=nickname,
            password=password,
            username=username,
        )

    async def saveFile(self):
        """通过文件流存储到本地"""
        return await self.call_api("file.save")

    async def statFile(self, *, objectName: str):
        """获取客户端的信息"""
        return await self.call_api("file.stat", objectName=objectName)

    async def authToken(self, *, appId: str, token: str, capability: Optional[list[str]] = Undefined) -> bool:
        """验证token"""
        return await self.call_api("openapi.app.authToken", appId=appId, token=token, capability=capability)

    async def createApp(self, *, appDesc: str, appIcon: str, appName: str):
        """创建一个第三方应用"""
        return await self.call_api("openapi.app.create", appDesc=appDesc, appIcon=appIcon, appName=appName)

    async def deleteApp(self, *, appId: str) -> bool:
        """删除开放平台应用"""
        return await self.call_api("openapi.app.delete", appId=appId)

    async def loginUser(
        self, *, password: str, email: Optional[str] = Undefined, username: Optional[str] = Undefined
    ) -> TokenInfo:
        """标准登录API"""
        return TypeAdapter(TokenInfo).validate_python(
            await self.call_api("user.login", email=email, password=password, username=username)
        )

    async def quitGroup(self, *, groupId: str):
        """退群"""
        return await self.call_api("group.quitGroup", groupId=groupId)

    async def updateAck(self, *, converseId: str, lastMessageId: str):
        """更新用户在会话中已读的最后一条消息"""
        return await self.call_api("chat.ack.update", converseId=converseId, lastMessageId=lastMessageId)

    async def addBotUser(self, *, appId: str, groupId: str):
        """在群组中添加机器人用户"""
        return await self.call_api("openapi.integration.addBotUser", appId=appId, groupId=groupId)

    async def addRequest(self, *, to: str, message: Optional[str] = Undefined) -> AddFriendRequestRet:
        """发送好友申请(message好像没用, 请求处理界面看不到message).不存在的id也能发送成功.不符合格式的id会报错."""
        return TypeAdapter(AddFriendRequestRet).validate_python(
            await self.call_api("friend.request.add", to=to, message=message)
        )

    async def allRelated(self) -> list[AddFriendRequestRet]:
        """所有与自己相关的好友请求, 包括自己发出的和别人发给自己的"""
        return TypeAdapter(list[AddFriendRequestRet]).validate_python(await self.call_api("friend.request.allRelated"))

    async def clearInbox(self) -> bool:
        """清空所有的收件箱内容"""
        return await self.call_api("chat.inbox.clear")

    async def setAppInfo(self, *, appId: str, fieldValue: str, fieldName: Literal["appName", "appDesc", "appIcon"]):
        """修改应用信息"""
        return await self.call_api("openapi.app.setAppInfo", appId=appId, fieldName=fieldName, fieldValue=fieldValue)

    async def getMessage(self, *, messageId: str) -> MessageRet:
        """获取消息"""
        return TypeAdapter(MessageRet).validate_python(
            await self.call_api("chat.message.getMessage", messageId=messageId)
        )

    async def addConverse(self, *, converseId: str):
        """加入或创建会话"""
        return await self.call_api("user.dmlist.addConverse", converseId=converseId)

    async def addReaction(self, *, emoji: str, messageId: str) -> bool:
        """添加消息表情"""
        return await self.call_api("chat.message.addReaction", emoji=emoji, messageId=messageId)

    async def applyInvite(self, *, code: str):
        """通过邀请码加群"""
        return await self.call_api("group.invite.applyInvite", code=code)

    async def createGroup(self, *, name: str, panels: list[Union[Panel, dict]]) -> GroupInfo:
        """创建群组"""
        return TypeAdapter(GroupInfo).validate_python(
            await self.call_api("group.createGroup", name=name, panels=panels)
        )

    async def denyRequest(self, *, requestId: str):
        """拒绝好友请求"""
        return await self.call_api("friend.request.deny", requestId=requestId)

    async def getUserInfo(self, *, userId: str) -> UserInfo:
        """获取用户信息"""
        return TypeAdapter(UserInfo).validate_python(await self.call_api("user.getUserInfo", userId=userId))

    async def sendMessage(
        self,
        *,
        content: str,
        converseId: str,
        meta: Optional[Union[dict, MessageMetaDict]] = Undefined,
        plain: Optional[str] = Undefined,
        groupId: Optional[str] = Undefined,
    ) -> MessageRet:
        """发送消息"""
        return TypeAdapter(MessageRet).validate_python(
            await self.call_api(
                "chat.message.sendMessage",
                meta=meta,
                plain=plain,
                content=content,
                groupId=groupId,
                converseId=converseId,
            )
        )

    async def verifyEmail(self, *, email: str):
        """验证用户邮箱, 会往邮箱发送一个 OTP 作为唯一标识
        需要在注册的时候带上"""
        return await self.call_api("user.verifyEmail", email=email)

    async def configClient(self) -> ClientConfig:
        """获取客户端配置"""
        return TypeAdapter(ClientConfig).validate_python(await self.call_api("config.client"))

    async def deleteInvite(self, *, groupId: str, inviteId: str):
        """删除邀请码"""
        return await self.call_api("group.invite.deleteInvite", groupId=groupId, inviteId=inviteId)

    async def getGroupData(self, *, name: str, groupId: str) -> GroupDataRet:
        return await self.call_api("group.extra.getGroupData", name=name, groupId=groupId)

    async def getPanelData(self, *, name: str, groupId: str, panelId: str) -> dict:
        """获取面板数据"""
        return await self.call_api("group.extra.getPanelData", name=name, groupId=groupId, panelId=panelId)

    async def isGroupOwner(self, *, groupId: str):
        """是否为创建者"""
        return await self.call_api("group.isGroupOwner", groupId=groupId)

    async def listRegistry(self):
        """getPluginList"""
        return await self.call_api("plugin.registry.list")

    async def removeFriend(self, *, friendUserId: str):
        """移除单项好友关系"""
        return await self.call_api("friend.removeFriend", friendUserId=friendUserId)

    async def resolveToken(self, *, token: str) -> TokenInfo:
        """获取token信息"""
        return TypeAdapter(TokenInfo).validate_python(await self.call_api("user.resolveToken", token=token))

    async def acceptRequest(self, *, requestId: str):
        """接受好友请求"""
        return await self.call_api("friend.request.accept", requestId=requestId)

    async def cancelRequest(self, *, requestId: str):
        """撤销申请好友请求. 填不存在的requestId会报错, 不符合格式的也会报错"""
        return await self.call_api("friend.request.cancel", requestId=requestId)

    async def checkIsFriend(self, *, targetId: str) -> bool:
        """检查对方是否为自己好友"""
        return await self.call_api("friend.checkIsFriend", targetId=targetId)

    async def deleteMessage(self, *, messageId: str) -> bool:
        """删除消息"""
        return await self.call_api("chat.message.deleteMessage", messageId=messageId)

    async def gatewayHealth(self) -> Health:
        """获取网关健康状态"""
        return TypeAdapter(Health).validate_python(await self.call_api("gateway.health"))

    async def getAllFriends(self) -> list[dict[str, str]]:
        """获取全部好友的ID
        [{'id': '***'}]"""
        return await self.call_api("friend.getAllFriends")

    async def getUserGroups(self) -> list[GroupInfo]:
        """获取用户的群组"""
        return TypeAdapter(list[GroupInfo]).validate_python(await self.call_api("group.getUserGroups"))

    async def recallMessage(self, *, messageId: str) -> MessageRet:
        """撤回消息, 大于15分钟的消息无法撤回, 会报错"""
        return TypeAdapter(MessageRet).validate_python(
            await self.call_api("chat.message.recallMessage", messageId=messageId)
        )

    async def resetPassword(self, *, otp: str, email: str, password: str) -> bool:
        """重置密码"""
        return await self.call_api("user.resetPassword", otp=otp, email=email, password=password)

    async def saveGroupData(self, *, data: str, name: str, groupId: str) -> bool:
        return await self.call_api("group.extra.saveGroupData", data=data, name=name, groupId=groupId)

    async def savePanelData(self, *, data: str, name: str, groupId: str, panelId: str) -> bool:
        """保存面板数据"""
        return await self.call_api("group.extra.savePanelData", data=data, name=name, groupId=groupId, panelId=panelId)

    async def searchMessage(
        self, *, text: str, converseId: str, groupId: Optional[str] = Undefined
    ) -> list[MessageRet]:
        """搜索消息"""
        return TypeAdapter(list[MessageRet]).validate_python(
            await self.call_api("chat.message.searchMessage", text=text, groupId=groupId, converseId=converseId)
        )

    async def setAppBotInfo(self, *, appId: str, fieldName: str, fieldValue: Any):
        """设置Bot的设置信息"""
        return await self.call_api("openapi.app.setAppBotInfo", appId=appId, fieldName=fieldName, fieldValue=fieldValue)

    async def forgetPassword(self, *, email: str):
        """忘记密码
        流程: 发送一个链接到远程，点开后可以直接重置密码"""
        return await self.call_api("user.forgetPassword", email=email)

    async def getAllConverse(self) -> list[str]:
        """获取所有会话"""
        return await self.call_api("user.dmlist.getAllConverse")

    async def getPermissions(self, *, groupId: str) -> list[str]:
        """获取群组成员权限(对外)"""
        return await self.call_api("group.getPermissions", groupId=groupId)

    async def modifyPassword(self, *, newPassword: str, oldPassword: str):
        """修改密码(好像没啥用)"""
        return await self.call_api("user.modifyPassword", newPassword=newPassword, oldPassword=oldPassword)

    async def removeConverse(self, *, converseId: str) -> dict:
        """删除会话
        {"modifiedCount":1}"""
        return await self.call_api("user.dmlist.removeConverse", converseId=converseId)

    async def removeReaction(self, *, emoji: str, messageId: str) -> bool:
        """删除消息表情"""
        return await self.call_api("chat.message.removeReaction", emoji=emoji, messageId=messageId)

    async def checkTokenValid(self, *, token: str):
        """检查授权是否可用"""
        return await self.call_api("user.checkTokenValid", token=token)

    async def checkUserOnline(self, *, userIds: list[str]) -> list[bool]:
        """检查用户是否在线"""
        return await self.call_api("gateway.checkUserOnline", userIds=userIds)

    async def createGroupRole(self, *, groupId: str, roleName: str, permissions: list[str]) -> GroupInfo:
        """创建群用户组"""
        return TypeAdapter(GroupInfo).validate_python(
            await self.call_api("group.createGroupRole", groupId=groupId, roleName=roleName, permissions=permissions)
        )

    async def deleteGroupRole(self, *, roleId: str, groupId: str) -> GroupInfo:
        """删除群用户组"""
        return TypeAdapter(GroupInfo).validate_python(
            await self.call_api("group.deleteGroupRole", roleId=roleId, groupId=groupId)
        )

    async def editGroupInvite(
        self, *, code: str, groupId: str, expireAt: Optional[int] = Undefined, usageLimit: Optional[int] = Undefined
    ) -> bool:
        """编辑群组邀请码"""
        return await self.call_api(
            "group.invite.editGroupInvite", code=code, groupId=groupId, expireAt=expireAt, usageLimit=usageLimit
        )

    async def ensurePluginBot(self, *, botId: str, nickname: str, avatar: Optional[str] = Undefined):
        return await self.call_api("user.ensurePluginBot", botId=botId, avatar=avatar, nickname=nickname)

    async def findAndJoinRoom(self) -> FindAndJoinRoomRet:
        """查找用户相关的所有会话并加入房间"""
        return TypeAdapter(FindAndJoinRoomRet).validate_python(await self.call_api("chat.converse.findAndJoinRoom"))

    async def getUserInfoList(self, *, userIds: list[str]) -> list[UserInfo]:
        """获取多个用户信息"""
        return TypeAdapter(list[UserInfo]).validate_python(await self.call_api("user.getUserInfoList", userIds=userIds))

    async def getUserSettings(self) -> dict:
        """获取用户设置"""
        return await self.call_api("user.getUserSettings")

    async def muteGroupMember(self, *, muteMs: int, groupId: str, memberId: str) -> bool:
        """禁言群成员"""
        return await self.call_api("group.muteGroupMember", muteMs=muteMs, groupId=groupId, memberId=memberId)

    async def setAppOAuthInfo(self, *, appId: str, fieldName: str, fieldValue: Any):
        """设置OAuth的设置信息"""
        return await self.call_api(
            "openapi.app.setAppOAuthInfo", appId=appId, fieldName=fieldName, fieldValue=fieldValue
        )

    async def setUserSettings(self, *, settings: dict) -> dict:
        """修改用户设置"""
        return await self.call_api("user.setUserSettings", settings=settings)

    async def updateUserExtra(self, *, fieldName: str, fieldValue: Any):
        """修改用户额外数据"""
        return await self.call_api("user.updateUserExtra", fieldName=fieldName, fieldValue=fieldValue)

    async def updateUserField(self, *, fieldName: str, fieldValue: Any) -> UserInfo:
        """更改用户信息"""
        return TypeAdapter(UserInfo).validate_python(
            await self.call_api("user.updateUserField", fieldName=fieldName, fieldValue=fieldValue)
        )

    async def createDMConverse(self, *, memberIds: list[str]) -> ConverseInfo:
        """创建会话"""
        return TypeAdapter(ConverseInfo).validate_python(
            await self.call_api("chat.converse.createDMConverse", memberIds=memberIds)
        )

    async def createGroupPanel(
        self,
        *,
        name: str,
        type_: int,
        groupId: str,
        meta: Optional[dict] = Undefined,
        parentId: Optional[str] = Undefined,
        provider: Optional[str] = Undefined,
        pluginPanelName: Optional[str] = Undefined,
    ) -> dict:
        """创建群组面板"""
        return await self.call_api(
            "group.createGroupPanel",
            name=name,
            meta=meta,
            type=type_,
            groupId=groupId,
            parentId=parentId,
            provider=provider,
            pluginPanelName=pluginPanelName,
        )

    async def deleteGroupPanel(self, *, groupId: str, panelId: str) -> GroupInfo:
        """删除群组面板"""
        return TypeAdapter(GroupInfo).validate_python(
            await self.call_api("group.deleteGroupPanel", groupId=groupId, panelId=panelId)
        )

    async def ensureOpenapiBot(self, *, botId: str, nickname: str, avatar: Optional[str] = Undefined) -> BotInfoRet:
        """确保第三方开放平台机器人存在(没有则自动创建)"""
        return TypeAdapter(BotInfoRet).validate_python(
            await self.call_api("user.ensureOpenapiBot", botId=botId, avatar=avatar, nickname=nickname)
        )

    async def findConverseInfo(self, *, converseId: str) -> ConverseInfo:
        """获取会话信息, 只能用于DM(私信)/Multi(多人会话)"""
        return TypeAdapter(ConverseInfo).validate_python(
            await self.call_api("chat.converse.findConverseInfo", converseId=converseId)
        )

    async def findInviteByCode(self, *, code: str) -> Optional[InviteCodeInfo]:
        """通过邀请码查找群组邀请信息"""
        return TypeAdapter(Optional[InviteCodeInfo]).validate_python(
            await self.call_api("group.invite.findInviteByCode", code=code)
        )

    async def findOpenapiBotId(self, *, email: str):
        """根据用户邮箱获取开放平台机器人id"""
        return await self.call_api("user.findOpenapiBotId", email=email)

    async def modifyGroupPanel(
        self,
        *,
        name: str,
        type_: int,
        groupId: str,
        panelId: str,
        meta: Optional[dict] = Undefined,
        provider: Optional[str] = Undefined,
        permissionMap: Optional[dict] = Undefined,
        pluginPanelName: Optional[str] = Undefined,
        fallbackPermissions: Optional[list[str]] = Undefined,
    ):
        """修改群组面板"""
        return await self.call_api(
            "group.modifyGroupPanel",
            meta=meta,
            name=name,
            type=type_,
            groupId=groupId,
            panelId=panelId,
            provider=provider,
            permissionMap=permissionMap,
            pluginPanelName=pluginPanelName,
            fallbackPermissions=fallbackPermissions,
        )

    async def setAppCapability(self, *, appId: str, capability: list[str]):
        """设置应用开放的能力"""
        return await self.call_api("openapi.app.setAppCapability", appId=appId, capability=capability)

    async def updateGroupField(self, *, groupId: str, fieldName: str, fieldValue: Any):
        """更新群组字段"""
        return await self.call_api(
            "group.updateGroupField", groupId=groupId, fieldName=fieldName, fieldValue=fieldValue
        )

    async def createGroupInvite(self, *, groupId: str, inviteType: Literal["normal", "permanent"]) -> InviteCodeInfo:
        """创建群组邀请码"""
        return TypeAdapter(InviteCodeInfo).validate_python(
            await self.call_api("group.invite.createGroupInvite", groupId=groupId, inviteType=inviteType)
        )

    async def deleteGroupMember(self, *, groupId: str, memberId: str):
        """删除群成员"""
        return await self.call_api("group.deleteGroupMember", groupId=groupId, memberId=memberId)

    async def getGroupBasicInfo(self, *, groupId: str) -> BaseGroupInfo:
        """获取群基本消息"""
        return TypeAdapter(BaseGroupInfo).validate_python(
            await self.call_api("group.getGroupBasicInfo", groupId=groupId)
        )

    async def setFriendNickname(self, *, nickname: str, targetId: str) -> bool:
        """设置好友昵称"""
        return await self.call_api("friend.setFriendNickname", nickname=nickname, targetId=targetId)

    async def updateGroupConfig(self, *, groupId: str, configName: str, configValue: Any):
        """更新群组配置"""
        return await self.call_api(
            "group.updateGroupConfig", groupId=groupId, configName=configName, configValue=configValue
        )

    async def claimTemporaryUser(
        self,
        *,
        email: str,
        userId: str,
        password: str,
        emailOTP: Optional[str] = Undefined,
        username: Optional[str] = Undefined,
    ):
        """认领临时用户"""
        return await self.call_api(
            "user.claimTemporaryUser",
            email=email,
            userId=userId,
            emailOTP=emailOTP,
            password=password,
            username=username,
        )

    async def fetchNearbyMessage(
        self, *, messageId: str, converseId: str, num: Optional[int] = Undefined, groupId: Optional[str] = Undefined
    ) -> list[MessageRet]:
        """获取指定消息的上下文"""
        return TypeAdapter(list[MessageRet]).validate_python(
            await self.call_api(
                "chat.message.fetchNearbyMessage", num=num, groupId=groupId, messageId=messageId, converseId=converseId
            )
        )

    async def verifyEmailWithOTP(self, *, emailOTP: str):
        """验证邮箱"""
        return await self.call_api("user.verifyEmailWithOTP", emailOTP=emailOTP)

    async def buildFriendRelation(self, *, user1: str, user2: str):
        """构建好友关系"""
        return await self.call_api("friend.buildFriendRelation", user1=user1, user2=user2)

    async def createTemporaryUser(self, *, nickname: str) -> TemporaryUserInfo:
        """创建临时用户"""
        return TypeAdapter(TemporaryUserInfo).validate_python(
            await self.call_api("user.createTemporaryUser", nickname=nickname)
        )

    async def updateGroupRoleName(self, *, roleId: str, groupId: str, roleName: str) -> GroupInfo:
        """更新群用户组名称"""
        return TypeAdapter(GroupInfo).validate_python(
            await self.call_api("group.updateGroupRoleName", roleId=roleId, groupId=groupId, roleName=roleName)
        )

    async def fetchConverseMessage(self, *, converseId: str, startId: Optional[str] = Undefined) -> list[MessageRet]:
        """获取会话消息"""
        return TypeAdapter(list[MessageRet]).validate_python(
            await self.call_api("chat.message.fetchConverseMessage", startId=startId, converseId=converseId)
        )

    async def getAllGroupInviteCode(self, *, groupId: str) -> list[InviteCodeInfo]:
        """获取所有群组邀请码"""
        return TypeAdapter(list[InviteCodeInfo]).validate_python(
            await self.call_api("group.invite.getAllGroupInviteCode", groupId=groupId)
        )

    async def appendGroupMemberRoles(self, *, groupId: str, roles: list[str], memberIds: list[str]):
        """添加群用户组成员"""
        return await self.call_api("group.appendGroupMemberRoles", roles=roles, groupId=groupId, memberIds=memberIds)

    async def removeGroupMemberRoles(self, *, groupId: str, roles: list[str], memberIds: list[str]):
        """移除群用户组成员"""
        return await self.call_api("group.removeGroupMemberRoles", roles=roles, groupId=groupId, memberIds=memberIds)

    async def appendDMConverseMembers(self, *, converseId: str, memberIds: list[str]):
        """在多人会话中添加成员"""
        return await self.call_api("chat.converse.appendDMConverseMembers", memberIds=memberIds, converseId=converseId)

    async def getGroupLobbyConverseId(self, *, groupId: str) -> str:
        """获取群组大厅的会话ID"""
        return await self.call_api("group.getGroupLobbyConverseId", groupId=groupId)

    async def searchUserWithUniqueName(self, *, uniqueName: str) -> Optional[UserInfo]:
        """根据唯一名搜索用户"""
        return TypeAdapter(Optional[UserInfo]).validate_python(
            await self.call_api("user.searchUserWithUniqueName", uniqueName=uniqueName)
        )

    async def fetchConverseLastMessages(self, *, converseIds: list[str]) -> list[LastMessages]:
        """获取多个会话的最后一条消息"""
        return TypeAdapter(list[LastMessages]).validate_python(
            await self.call_api("chat.message.fetchConverseLastMessages", converseIds=converseIds)
        )

    async def getJoinedGroupAndPanelIds(self) -> GroupAndPanelIds:
        """获取加入的群组和面板ID"""
        return TypeAdapter(GroupAndPanelIds).validate_python(await self.call_api("group.getJoinedGroupAndPanelIds"))

    async def updateGroupRolePermission(self, *, roleId: str, groupId: str, permissions: list[str]) -> GroupInfo:
        """更新群用户组权限"""
        return TypeAdapter(GroupInfo).validate_python(
            await self.call_api(
                "group.updateGroupRolePermission", roleId=roleId, groupId=groupId, permissions=permissions
            )
        )
