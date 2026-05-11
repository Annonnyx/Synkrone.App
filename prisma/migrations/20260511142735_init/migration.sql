-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "discordId" TEXT NOT NULL,
    "username" TEXT NOT NULL,
    "email" TEXT,
    "avatar" TEXT,
    "roles" TEXT[],
    "kronesBalance" INTEGER NOT NULL DEFAULT 1000,
    "kronesSpent" INTEGER NOT NULL DEFAULT 0,
    "subscriptionId" TEXT,
    "boxQuotaMb" INTEGER NOT NULL DEFAULT 500,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Subscription" (
    "id" TEXT NOT NULL,
    "plan" TEXT NOT NULL,
    "kronesPerMonth" INTEGER NOT NULL,
    "priceEuros" DOUBLE PRECISION NOT NULL,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "renewsAt" TIMESTAMP(3) NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'ACTIVE',

    CONSTRAINT "Subscription_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "KroneTransaction" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "amount" INTEGER NOT NULL,
    "reason" TEXT NOT NULL,
    "relatedId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "KroneTransaction_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Bot" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "botName" TEXT NOT NULL,
    "prefix" TEXT NOT NULL DEFAULT '!',
    "slashCommands" BOOLEAN NOT NULL DEFAULT false,
    "cogs" TEXT[],
    "kronesConsumed" INTEGER NOT NULL DEFAULT 0,
    "status" TEXT NOT NULL DEFAULT 'OFFLINE',
    "groupId" TEXT,
    "encPath" TEXT NOT NULL,
    "dirPath" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Bot_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BotGroup" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "botCount" INTEGER NOT NULL DEFAULT 0,
    "maxBots" INTEGER NOT NULL DEFAULT 10,
    "status" TEXT NOT NULL DEFAULT 'RUNNING',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "BotGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BotStats" (
    "id" TEXT NOT NULL,
    "botId" TEXT NOT NULL,
    "serversCount" INTEGER NOT NULL DEFAULT 0,
    "commandsTotal" INTEGER NOT NULL DEFAULT 0,
    "errorsLast24h" INTEGER NOT NULL DEFAULT 0,
    "uptimeSeconds" INTEGER NOT NULL DEFAULT 0,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "BotStats_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MinecraftServer" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "serverName" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "ramMb" INTEGER NOT NULL,
    "storageQuotaMb" INTEGER NOT NULL DEFAULT 5120,
    "storageUsedMb" INTEGER NOT NULL DEFAULT 0,
    "gameMode" TEXT NOT NULL DEFAULT 'SURVIVAL',
    "difficulty" TEXT NOT NULL DEFAULT 'NORMAL',
    "pvp" BOOLEAN NOT NULL DEFAULT true,
    "maxPlayers" INTEGER NOT NULL DEFAULT 20,
    "status" TEXT NOT NULL DEFAULT 'OFFLINE',
    "dirPath" TEXT NOT NULL,
    "sftpUser" TEXT NOT NULL,
    "sftpPasswordEnc" TEXT NOT NULL,
    "pm2Name" TEXT NOT NULL,
    "kronesPerMonth" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "MinecraftServer_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MinecraftBackup" (
    "id" TEXT NOT NULL,
    "serverId" TEXT NOT NULL,
    "filePath" TEXT NOT NULL,
    "sizeMb" DOUBLE PRECISION NOT NULL,
    "type" TEXT NOT NULL DEFAULT 'AUTO',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "MinecraftBackup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Site" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "projectName" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "siteType" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "url" TEXT,
    "dirPath" TEXT,
    "nginxConfig" TEXT,
    "kronesPerMonth" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Site_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "App" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "appName" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "runtime" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "url" TEXT,
    "dirPath" TEXT,
    "pm2Name" TEXT,
    "kronesPerMonth" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "App_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CommandDefinition" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "module" TEXT NOT NULL,
    "priceKr" INTEGER NOT NULL,
    "premium" BOOLEAN NOT NULL DEFAULT false,
    "usage" TEXT NOT NULL,
    "permissions" JSONB NOT NULL,
    "envVars" JSONB NOT NULL,
    "version" TEXT NOT NULL DEFAULT '1.0.0',

    CONSTRAINT "CommandDefinition_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AdminLog" (
    "id" TEXT NOT NULL,
    "actorId" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "target" TEXT,
    "details" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AdminLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_discordId_key" ON "User"("discordId");

-- CreateIndex
CREATE UNIQUE INDEX "User_subscriptionId_key" ON "User"("subscriptionId");

-- CreateIndex
CREATE UNIQUE INDEX "BotGroup_name_key" ON "BotGroup"("name");

-- CreateIndex
CREATE UNIQUE INDEX "BotStats_botId_key" ON "BotStats"("botId");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_subscriptionId_fkey" FOREIGN KEY ("subscriptionId") REFERENCES "Subscription"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "KroneTransaction" ADD CONSTRAINT "KroneTransaction_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Bot" ADD CONSTRAINT "Bot_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Bot" ADD CONSTRAINT "Bot_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES "BotGroup"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BotStats" ADD CONSTRAINT "BotStats_botId_fkey" FOREIGN KEY ("botId") REFERENCES "Bot"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MinecraftServer" ADD CONSTRAINT "MinecraftServer_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MinecraftBackup" ADD CONSTRAINT "MinecraftBackup_serverId_fkey" FOREIGN KEY ("serverId") REFERENCES "MinecraftServer"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Site" ADD CONSTRAINT "Site_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "App" ADD CONSTRAINT "App_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
